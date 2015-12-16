# Estimate the distributions of mobility graph links
library(dplyr)
library(igraph)
library(magicaxis)
library(sfsmisc)
library(movr)

fm.d <- read.csv("data/scl_fine_p06_fm_i24h", sep=',', header=F, stringsAsFactors=F)
colnames(fm.d) = c("interval", "from", "to", "unique", "total")
fm.d$interval = as.POSIXct(fm.d$interval * 3600 * 24, origin="1970-01-01 00:00:00", tz="GMT")

fm.h <- read.csv("data/hcl_mesos0825_fm_i6h", sep=',', header=F, stringsAsFactors=F)
colnames(fm.h) = c("interval", "from", "to", "unique", "total")
fm.h$interval = as.POSIXct(fm.h$interval * 3600 * 6, origin="1970-01-01 00:00:00", tz="Asia/Shanghai")
fm.h <- fm.h[fm.h$interval==as.POSIXct("2012-08-25 14:00:00", tz="Asia/Shanghai"), ]

trips <- read.csv("data/tts_trips.dat", head=T, sep=",")
trips <- trips[complete.cases(trips), ]
fm.t <- trips %>% dplyr::filter(DAYNO == 1) %>%
  with(flowmap2(uid, locno, as.numeric(stime), as.numeric(etime))) %>%
  dplyr::filter(from != to) %>%
  mutate(from = as.numeric(from), to = as.numeric(to))

graph.d <- as.undirected(graph.data.frame(fm.d[, c("from", "to")]))
graph.h <- as.undirected(graph.data.frame(fm.h[, c("from", "to")]))
graph.t <- as.undirected(graph.data.frame(fm.t[, c("from", "to")]))

degree.d <- as.numeric(degree(graph.d))
hist.d <- hist(degree.d, breaks=c(0:max(degree.d)), plot=F)
degree.h <- as.numeric(degree(graph.h))
hist.h <- hist(degree.h, breaks=c(0:max(degree.h)), plot=F)
degree.t <- as.numeric(degree(graph.t))
hist.t <- hist(degree.t, breaks=c(0:max(degree.t)), plot=F)

pdf("figures/powerlaw.pdf", width=6.5, height=5)
par(mar=c(3.5, 3.5, 1, 1))

## Senegal
x = ceiling(hist.d$mids)
y = hist.d$density
magplot(x, y, log="xy", pch=21, bg='royalblue', cex=1.2, col='royalblue',
        xlim=c(1, 200), ylim=c(10^-5, 0.7), xlab="Degree of Vertex", ylab="PDF", side=1:4, labels=c(T,T,F,F))
fit_truncated_power_law(x, y, x0=80)

## Hangzhou
x = ceiling(hist.h$mids)
y = hist.h$density
points(x, y, log="xy", pch=21, cex=1.2, col='orangered', bg='orangered')
fit_truncated_power_law(x, y, x0=25)

## Chicago
x = ceiling(hist.t$mids)
select=c(3:length(x))
x = x[select]
y = hist.t$density[select]
points(x, y, log='xy', pch=21, bg=colors()[558], col="white", cex=1.2)
fit_power_law(x, y, x0 = 13)

dev.off()

