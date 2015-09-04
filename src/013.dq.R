library(movr)
library(ggplot2)
library(magicaxis)
library(scatterplot3d)

##+++++++++++++++++++++++++++++<<<< FUNCTIONS ++++++++++++++++++++++++++++++++++

dq_daily_info <- function(user, time,  n = 48) {
  interval = 3600 * 24 / n
  int = as.numeric(time) %/% (86400 / n) %% n
  dd = time %/% 86400
  
  df <- data.frame(user=user, time=time, int=int, dd=dd)
  tinfo <- mov_site %>% group_by(user, dd) %>%
    summarise(obs=length(time), ints=length(unique(int)), locs=length(unique(loc)))
  tinfo
}

plot_daily_info <- function(dq.daily.info, n=48) {
  interval = 3600 * 24 / n
  tinfo <- dq.daily.info
  
  par(mfrow=c(3,3), mar=c(3.5, 3.5, 1, 1))
  pcol = "black"
  pbg = colors()[500]
  labs=c(T,T,F,F)
  
  # ECDF of Intervals
  cdf1 <- ecdf(tinfo$ints/2)
  icdf1 <- inv_ecdf(cdf1)
  magplot(cdf1, pch=22, col=pcol, bg=pbg, labels=labs, side=1:4,
          lty=1, xlab="Intervals", ylab="CDF", xlim=c(0, 24),
          panel.first = rect(-1, -1, 3, 2, col=colors()[236], border=NA))
  abline(v=3, lty=2)
  
  # ECDF of Observations
  cdf2 <- ecdf(tinfo$obs)
  icdf2 <- inv_ecdf(cdf2)
  magplot(cdf2, pch=22, col=pcol, bg=pbg, labels=labs, side=1:4,
          lty=1, xlab="Observations", ylab="CDF", log="x", xlim=c(1, max(tinfo$obs)),
          panel.first = rect(1e-10, -1, icdf2(0.5), 2, col=colors()[236], border=NA))
  abline(v=icdf2(0.5), lty=2)
  
  # ECDF of Locations
  cdf3 <- ecdf(tinfo$locs)
  icdf3 <- inv_ecdf(cdf3)
  magplot(cdf3, pch=22, col=pcol, bg=pbg, labels=labs, side=1:4,
          lty=1, xlab="Visited Locations", ylab="CDF", log="x", xlim=c(1, max(tinfo$obs)),
          panel.first = rect(1e-10, -1, icdf3(0.5), 2, col=colors()[236], border=NA))
  abline(v=icdf3(0.5), lty=2)
  
  # Intervals
  tf <- tinfo %>% group_by(ints) %>% summarise(total=length(user))
  tf <- tf[order(tf$ints), ]
  magplot(tf$ints*24/n, tf$total, pch=21, col=pcol, bg=pbg, labels=labs,
          log="y", xlab="Intervals", ylab = "Freqency", xlim=c(0, 24), side=1:4,
          panel.first = rect(-1, 1e-10, 3, 1e10, col=colors()[236], border=NA))
  abline(v=3, lty=2)
  
  # Observations
  tf <- tinfo %>% group_by(obs) %>% summarise(total=length(user))
  tf <- tf[order(tf$obs), ]
  magplot(tf$obs, tf$total, pch=21, col=pcol, bg=pbg, labels=labs,
          log="xy", xlab="Observations", ylab = "Freqency", side=1:4,
          panel.first = rect(1e-10, 1e-10, icdf2(0.5), 1e10, col=colors()[236], border=NA))
  abline(v=icdf2(0.5), lty=2)
  
  # Locations
  tf <- tinfo %>% group_by(locs) %>% summarise(total=length(user))
  tf <- tf[order(tf$total), ]
  magplot(tf$locs, tf$total, pch=21, col=pcol, bg=pbg, labels=labs,
          log="xy", xlab="Visited Locations", ylab = "Freqency", side=1:4,
          panel.first = rect(1e-10, 1e-10, icdf3(0.5), 1e10, col=colors()[236], border=NA))
  abline(v=icdf3(0.5), lty=2)
  
  tinfo2 <- tinfo %>% group_by(user) %>%
    summarise(obs=mean(obs), ints=mean(ints), days=length(dd), locs=mean(locs))
  
  magplot(tinfo2$obs, tinfo2$locs, pch=".", log="xy", xlab="Observations", ylab="Locations")
  magplot(tinfo2$obs, tinfo2$ints, pch=".", log="xy", xlab="Observations", ylab="Intervals")
  magplot(tinfo2$locs, tinfo2$ints, pch=".", log="xy", xlab="Locations", ylab="Intervals")
}

## The inverse emperical CDF
inv_ecdf <- function(f){
  x <- environment(f)$x
  y <- environment(f)$y
  approxfun(y, x)
}

##+++++++++++++++++++++++++++++>>>> FUNCTIONS ++++++++++++++++++++++++++++++++++


mov_site <- readRDS("rdata/dsp10cl.rds")
colnames(mov_site) <- c("user", "time", "loc")

mov_site <- mov_site %>% mutate(
  tt = as.POSIXct(time, origin="1970-01-01", tz="GMT"),
  int = time %/% 1800 %% 48,
  dd = time %/% 86400 )

## estimate user's data quality at daily scale
tinfo <- dq_daily_info(mov_site$user, mov_site$time)
plot_daily_info(tinfo)

## estimate location and mobility network quality

