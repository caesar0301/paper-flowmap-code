# Estimate the distributions of mobility graph links
library(dplyr)
library(igraph)
library(magicaxis)
library(sfsmisc)

fm.h <- read.csv("data/fm_hz_i6h_m5.dat", sep=',', header=F, stringsAsFactors=F)
colnames(fm.h) = c("interval", "from", "to", "unique", "total")
fm.h$interval = as.POSIXct(fm.h$interval * 3600 * 6, origin="1970-01-01 00:00:00", tz="Asia/Shanghai")
fm.h <- fm.h[fm.h$interval==as.POSIXct("2012-08-19 14:00:00", tz="Asia/Shanghai"), ]

fm.d <- read.csv("data/fm_dsp01_i6h_m5.dat", sep=',', header=F, stringsAsFactors=F)
colnames(fm.d) = c("interval", "from", "to", "unique", "total")
fm.d$interval = as.POSIXct(fm.d$interval * 3600 * 6, origin="1970-01-01 00:00:00", tz="GMT")
fm.d <- fm.d[fm.d$interval==as.POSIXct("2013-01-10 12:00:00", tz="GMT"), ]

fm.t <- readRDS("rdata/tts_fm.rds") %>% dplyr::filter(from != to) %>%
  mutate(from = as.numeric(from), to = as.numeric(to))
fm.t <- fm.t[fm.t$DAYNO == 2, ]

graph.h <- as.undirected(graph.data.frame(fm.h[, c("from", "to")]))
graph.d <- as.undirected(graph.data.frame(fm.d[, c("from", "to")]))
graph.t <- as.undirected(graph.data.frame(fm.t[, c("from", "to")]))

degree.h <- as.numeric(degree(graph.h))
hist.h <- hist(degree.h, breaks=c(0:max(degree.h)), plot=F)
degree.d <- as.numeric(degree(graph.d))
hist.d <- hist(degree.d, breaks=c(0:max(degree.d)), plot=F)
degree.t <- as.numeric(degree(graph.t))
hist.t <- hist(degree.t, breaks=c(0:max(degree.t)), plot=F)

###################### using optim
# trunpl <- function(par, x, y){
#   y[y==0] <- 10^-9 # supress Inf error
#   xo=par[1]
#   beta=par[2]
#   k=par[3]
#   est=((x-xo)^(-beta))*exp(-x/k)
#   sum((log(y) - log(est))^2)
# }
# 
# magplot(hist.h$mids, hist.h$density, log="xy", pch=21, bg=colors()[62], xlim=c(1, 100))
# f <- optim(par=c(0.2,0.1,20), trunpl, x=c(1:length(hist.d$density)), y=hist.d$density)
# x1=seq(1,100,1)
# y1=(f$par[1]*x1^ (-f$par[2])) * exp(-x1/f$par[3])
# lines(x1, y1, col=colors()[62])
# 
# points(hist.d$mids, hist.d$density, log="xy",  pch=21, bg=colors()[500])
# f <- optim(par=c(0.1,0.5,10), trunpl, x=c(1:length(hist.h$density)), y=hist.h$density)
# x1=seq(1,100,1)
# y1=((x1 - f$par[1]) ^ (-f$par[2])) * exp(- x1 / f$par[3])
# lines(x1, y1, col=colors()[500])
# 
# points(hist.t$mids, hist.t$density, log="xy", pch=21, bg=colors()[135])
# f <- optim(par=c(0.1,0.5,10), trunpl, x=c(1:length(hist.t$density)), y=hist.t$density)
# x1=seq(1,100,1)
# y1=((x1 - f$par[1]) ^ (-f$par[2])) * exp(- x1 / f$par[3])
# lines(x1, y1, col=colors()[135])

##################### fit gamma distribution
# magplot(hist.h$mids, hist.h$density, log="xy", pch=21, bg=colors()[62], xlim=c(1, 100))
# x <- degree.h
# f <- fitdistr(x, "gamma")
# x1 <- seq(1,100,1)
# y1 <- dgamma(x1, f$estimate[1], f$estimate[2])
# lines(x1, y1, col=colors()[62])
# 
# # test goodness-of-fit
# freq.os <- as.numeric(table(x))
# bins <- c(as.data.frame(table(x))$x)
# shape <- f$estimate[['shape']]
# rate <- f$estimate[['rate']]
# freq.ex <- c(pgamma(1, shape, rate))
# for( i in 2:length(bins)) {
#   freq.ex[i] <- pgamma(bins[i], shape, rate) - pgamma(bins[i-1], shape, rate)
# }
# chisq.test(freq.os, freq.ex)
# X-squared = 986, df = 957, p-value = 0.251
# cant reject void hypothesis!!

##################### use poweRlaw (fit CCDF)
# library(poweRlaw)
# library(sfsmisc)
# y = hist.d$counts + 1
# x = ceiling(hist.d$mids)
# pl = dislnorm$new(y)
# est = estimate_xmin(pl)
# pl$setXmin(est$xmin)
# est = estimate_pars(pl)
# pl$setPars(est$pars)
# plot(pl, xaxt="n", yaxt="n")
# eaxis(1, at=c(10^0, 10^1, 10^2, 10^3), log=TRUE)
# lines(pl)
# bootstrap(pl)

#####################
fit.exp <- function(x, y, ...) {
  start.trials.b <- c(0.01, 0.5, 1, 2, 4, 10, 100, 1000)
  start.trials.gamma <- c(0.01, 0.1, 1, 10)
  starts <- expand.grid(start.trials.b, start.trials.gamma)
  for (i in 1:nrow(starts)) {
    EXP <- try(nls(y ~ b * exp(-gamma * x), start=list(b=starts[i, 1], gamma=starts[i, 2]), ...),
              silent=TRUE)
    if (!inherits(EXP, "try-error")) 
      break
  }
  EXP
}

fit.pl <- function(x, y, ...) {
  start.trials.b <- c(0.01, 0.5, 1, 2, 4, 10, 100, 1000)
  start.trials.gamma <- c(0.01, 0.1, 1, 10)
  starts <- expand.grid(start.trials.b, start.trials.gamma)
  for (i in 1:nrow(starts)) {
    PL <- try(nls(y ~ b * x^(-gamma), start=list(b=starts[i, 1], gamma=starts[i, 2]), ...),
              silent=TRUE)
    if (!inherits(PL, "try-error")) 
      break
  }
  PL
}

fit.tpl <- function(x, y, ...) {
  start.trials.b <- c(0.01, 0.5, 1, 2, 4, 10, 100, 1000)
  start.trials.gamma <- c(0.01, 0.1, 1, 10, 100)
  start.trials.k <- 10^c(-4:4)
  start.trials.xo <- x
  starts <- expand.grid(start.trials.b, start.trials.gamma, start.trials.k, start.trials.xo)
  for (i in 1:nrow(starts)) {
      TPL <- try(nls(y ~ b * (x+xo)^(-gamma) * exp(-x/k), start=list(b=starts[i, 1], gamma=starts[i, 2], k=starts[i, 3], xo=starts[i, 4]), ...),
                silent=TRUE)
      if (!inherits(TPL, "try-error")) 
        break
  }
  TPL
}

pdf("figures/powerlaw.pdf", width=5, heigth=5)
par(mar=c(3.5, 3.5, 1, 1))

x = ceiling(hist.h$mids)
y = hist.h$density
m.tpl <- fit.tpl(x, y, nls.control(maxiter = 1000))
coef(m.tpl)
magplot(x, y, log="xy", pch=21, cex=1.2, col="white", bg=colors()[431], xlim=c(1, 70),
        ylim=c(10^-5, 0.7), side=1:4, labels=c(T,T,F,F), xlab="Degree of Vertex", ylab="PDF")
x1=x
y1=m.tpl$m$predict(x1)
lines(x1, y1, col=colors()[62], lwd=3)

x = ceiling(hist.d$mids)
y = hist.d$density
m.tpl <- fit.tpl(x, y, nls.control(maxiter = 1000))
coef(m.tpl)
points(x, y, pch=21, bg=colors()[20], cex=1.2, col="white")
x1=x
y1=m.tpl$m$predict(x1)
lines(x1, y1, col=colors()[500], lwd=3)

x = ceiling(hist.t$mids)
select=c(3:length(x))
x = x[select]
y = hist.t$density[select]
m.tpl <- fit.exp(x, y, nls.control(maxiter = 1000))
points(ceiling(hist.t$mids), hist.t$density, pch=21, bg=colors()[558], col="white", cex=1.2)
coef(m.tpl)
x1=x
y1=m.tpl$m$predict(x1)
lines(x1, y1, col=colors()[135], lwd=3)

dev.off()

