library(stringr)
library(movr)
library(magicaxis)

################################################
#  Dwelling time of all
################################################

## Read dwelling time for weekday and weekends
readDWTime <- function(fname) {
  conn <- file(fname, open='r')
  linn <- readLines(conn)
  dwtime <- c()
  lines <- sample(1:length(linn), 10000, replace=F)
  for (i in lines) {
    line <- linn[i]
    parts <- str_split(line, ',')[[1]]
    dwtime <- c(dwtime, as.numeric(parts[2:length(parts)]))
  }
  dwtime
}

mesos22 <- readDWTime('data/hcl_mesos0822_dtloc_all')
mesos25 <- readDWTime('data/hcl_mesos0825_dtloc_all')

bins <- seq(0,18,0.15) # logscale
hist22 <- hist(mesos22[mesos22>=0.1 & mesos22 <=18], breaks=bins, plot=F)
hist25 <- hist(mesos25[mesos25>=0.1 & mesos25 <=18], breaks=bins, plot=F)

plot_hist_fit <- function(histdat, col, ...) {
  # Plot PDF with fitted line
  x = histdat$mids
  y = histdat$density
  magplot(x, y, log='xy', side=1:4, labels=c(T,T,F,F), col=col, ...)
  # Truncated x range
  xtrunc <- (x<=14)
  x1=x[xtrunc]
  y1=y[xtrunc]
  lmm <- lm(log(y1) ~ log(x1))
  print(coef(lmm))
  logy2=as.numeric(predict(lmm, newdata=list(x=log(x1))))
  lines(exp(logy2) ~ x1, col='black', lwd=1.5)
}

## Do plotting
svg("figures/dwtime_pl.svg", width=5, height=5)
par(mar=c(3.5, 3.5, 1, 1))
cols <- c("orangered", "royalblue")

# Weekday
plot_hist_fit(hist22, pch=6, cex=1.2, col=cols[1],
              xlim=c(0.9, 18), ylim=c(10^-5, 1), lwd=1, 
              xlab="Dwelling Time (Hours)", ylab="PDF")

# Weekend (inset figure)
subplot( 
  plot_hist_fit(hist25, pch=0, cex=0.7, col=cols[2], 
                xlim=c(0.9, 18), ylim=c(10^-3, 1), lwd=1, xlab="", ylab=""), 
  x=grconvertX(c(0.05,0.6), from='npc'),
  y=grconvertY(c(0.05,0.6), from='npc'),
  type='fig', pars=list( mar=c(1.5,1.5,0,0)+0.1) )
dev.off()

################################################
#  Dwelling time of individuals
################################################

library(mixtools)

dt7d <- read.table('data/hcl_mesos7d_dtloc_log', skip=1, head=F, sep=',')
colnames(dt7d) = c('uid', seq(1,49))
breaks <- sfsmisc::lseq(0.01,100,50)

freq2raw <- function(v, breaks) {
  # convert frequency to raw sequence, given a set of breaks
  mids <- (breaks[1:length(breaks)-1] + breaks[2:length(breaks)]) * 0.5
  dat <- data.frame(V1=mids, V2=v)
  dat2 <- unlist(apply(dat, 1, function(x) rep(x[1], x[2])))
  as.numeric(dat2)
}

get_mixmodel_params <- function(user) {
  # Mixmodel fitted with original data
  v = as.numeric(user[2:50])
  r <- freq2raw(v, breaks)
  pars <- normalmixEM(r, k=2)
  res <- list()
  res$mu <- pars$mu
  res$sigma <- pars$sigma
  res$lambda <- pars$lambda
  res
}

# Plot individual's dwelling time
plot_user_dwelling_time <- function(user) {  
  v = as.numeric(user[2:50])
  nat_breaks = c(0.5, 1:length(v) + 0.5) # mids: 1...49
  r <- freq2raw(v, nat_breaks)
  # fit model on natural axis
  pars.ml <- normalmixEM(r, k=2)
  mu <- pars.ml$mu
  sigma <- pars.ml$sigma
  lambda <- pars.ml$lambda
  
  n <- length(r)
  z <- rbinom(n, 1, lambda[1])
  sim.mix <- z*rnorm(n, mu[1], sigma[1]) + (1-z)*rnorm(n, mu[2], sigma[2])
  
  w <- hist(r, breaks=nat_breaks, plot=FALSE)
  w <- w$density
  w[w==0] <- 0.0001
  
  barplot(w, axes=FALSE, col=colors()[140])
  magaxis(side=1:4, labels=c(F,T,F,F), xlab="Dwelling Time (hours)", ylab="Probability")
  lines(density(sim.mix), lty=1, col="#CC0033", lwd=2)
  
  # Ajust log labels
  at10 <- round(log10(breaks))
  atseq <- seq_along(at10)
  at <- seq(min(atseq), max(atseq), by=ceiling(length(at10)/length(unique(at10))))
  labels <-sapply(at10[at],function(i) as.expression(bquote(10^ .(i))))
  Axis(side=1, at=atseq[at], labels=labels, lty=NULL, tick=F)
}

svg("figures/dwtime_mesos7d_u68795.svg", width=5, height=3)
par(mar=c(3.5, 3.5, 1, 1))
par(lwd = 0.7)
plot_user_dwelling_time(dt7d[dt7d$uid==68795,])
print(get_mixmodel_params(user))
dev.off()


###############################################
## Save user's model parameters
A <- apply(dt7d[1:100,], 1, function(user) {
  res <- tryCatch({
    params <- get_mixmodel_params(user)
    as.numeric(unlist(params)) },
    error = function(e) {
      rep(-1, 6) }
  )
  c(user[1], res)
})

write.table(t(A), 'data/hcl_mesos7d_dtloc_log_model', sep=',', row.names=F, col.names=F)

################################################
#  Individual model parameter space
################################################

library(MASS)
library(fields)
library(scatterplot3d)

# Plot DT model WITHOUT location information
models <- read.csv('data/hcl_mesos7d_dt_log_model_clean', sep=',', head=T)
head(models)
dens2d <- kde2d(models$mu1, models$mu2)
x <- dens2d$x
y <- dens2d$y
z <- dens2d$z
# 2D
pdf('figures/hcl_mesos7d_dt_log_model_mu_2d.pdf', height=4, width=6)
par(mar=c(3, 3, 1, 1), mgp=c(1.5,0.5,0))
filled.contour(x,y,z,color=terrain.colors, xlab="Mu1 (H)", ylab="Mu2 (H)")
dev.off()
# 3D
pdf('figures/hcl_mesos7d_dt_log_model_mu_3d.pdf', height=6, width=8)
persp(x,y,z,col="lightblue", nticks=6,theta=60, phi=10,
      xlab="Mu1 (H)", ylab="Mu2 (H)", zlab="Probability")
dev.off()

dens2d <- kde2d(models$gamma1, models$gamma2)
x <- dens2d$x
y <- dens2d$y
z <- dens2d$z
# 2D
pdf('figures/hcl_mesos7d_dt_log_model_gamma_2d.pdf', height=4, width=6)
par(mar=c(3, 3, 1, 1), mgp=c(1.5,0.5,0))
filled.contour(x,y,z,color=terrain.colors, xlab="Gamma1 (H)", ylab="Gamma2 (H)")
dev.off()
# 3D
pdf('figures/hcl_mesos7d_dt_log_model_gamma_3d.pdf', height=6, width=8)
persp(x,y,z,col="lightblue", nticks=6,theta=145, phi=10,
      xlab="Gamma1 (H)", ylab="Gamma2 (H)", zlab="Probability")
dev.off()


# Plot DT model WITH location information
models <- read.csv('data/hcl_mesos7d_dtloc_log_model_clean', sep=',', head=T)
head(models)
dens2d <- kde2d(models$mu1, models$mu2)
x <- dens2d$x
y <- dens2d$y
z <- dens2d$z
# 2D
pdf('figures/hcl_mesos7d_dtloc_log_model_mu_2d.pdf', height=4, width=6)
par(mar=c(3, 3, 1, 1), mgp=c(1.5,0.5,0))
filled.contour(x,y,z,color=terrain.colors, xlab="Mu1 (H)", ylab="Mu2 (H)")
dev.off()
# 3D
pdf('figures/hcl_mesos7d_dtloc_log_model_mu_3d.pdf', height=6, width=8)
persp(x,y,z,col="lightblue", nticks=6,theta=60, phi=10,
      xlab="Mu1 (H)", ylab="Mu2 (H)", zlab="Probability")
dev.off()

dens2d <- kde2d(models$gamma1, models$gamma2)
x <- dens2d$x
y <- dens2d$y
z <- dens2d$z
# 2D
pdf('figures/hcl_mesos7d_dtloc_log_model_gamma_2d.pdf', height=4, width=6)
par(mar=c(3, 3, 1, 1), mgp=c(1.5,0.5,0))
filled.contour(x,y,z,color=terrain.colors, xlab="Gamma1 (H)", ylab="Gamma2 (H)")
dev.off()
# 3D
pdf('figures/hcl_mesos7d_dtloc_log_model_gamma_3d.pdf', height=6, width=8)
persp(x,y,z,col="lightblue", nticks=6,theta=145, phi=10,
      xlab="Gamma1 (H)", ylab="Gamma2 (H)", zlab="Probability")
dev.off()