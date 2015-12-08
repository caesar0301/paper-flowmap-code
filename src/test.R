library(mixtools)
library(movr)
library(magicaxis)

dt7d <- read.table('data/hcl_mesos7d_dt_log', skip=1, head=F, sep=',')
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

A <- apply(dt7d, 1, function(user) {
  res <- tryCatch({
    params <- get_mixmodel_params(user)
    as.numeric(unlist(params)) },
    error = function(e) {
      rep(-1, 6) }
  )
  c(user[1], res)
})

write.table(t(A), 'data/hcl_mesos7d_dt_log_model', sep=',', row.names=F, col.names=F)
