# Estimate the distributions of mobility graph links
library(movr)
library(igraph)
library(magicaxis)
library(sfsmisc)

## Senegal
fm.d <- read.csv("data/scl_fine_p12_fm_i24h", sep=',', header=F, stringsAsFactors=F)
colnames(fm.d) = c("interval", "from", "to", "unique", "total")
fm.d$interval = as.POSIXct(fm.d$interval * 3600 * 24, origin="1970-01-01 00:00:00", tz="GMT")
graph.d <- as.undirected(graph.data.frame(fm.d[, c("from", "to")]))
degree.d <- as.numeric(degree(graph.d))
hist.d <- hist(degree.d, breaks=c(0:max(degree.d)), plot=F)

## Hangzhou
fm.h <- read.csv("data/hcl_mesos0825_fm_i6h", sep=',', header=F, stringsAsFactors=F)
colnames(fm.h) = c("interval", "from", "to", "unique", "total")
fm.h$interval = as.POSIXct(fm.h$interval * 3600 * 6, origin="1970-01-01 00:00:00", tz="Asia/Shanghai")
# fm.h <- fm.h[fm.h$interval==as.POSIXct("2012-08-25 14:00:00", tz="Asia/Shanghai"), ]
graph.h <- as.undirected(graph.data.frame(fm.h[, c("from", "to")]))
degree.h <- as.numeric(degree(graph.h))
hist.h <- hist(degree.h, breaks=c(0:max(degree.h)), plot=F)

## Chicago
# trips <- read.csv("data/tts_trips.dat", head=T, sep=",")
# trips <- trips[complete.cases(trips), ]
# fm.t <- trips %>% dplyr::filter(DAYNO == 1) %>%
#   with(flowmap2(uid, locno, as.numeric(stime), as.numeric(etime))) %>%
#   dplyr::filter(from != to) %>%
#   mutate(from = as.numeric(from), to = as.numeric(to))
# graph.t <- as.undirected(graph.data.frame(fm.t[, c("from", "to")]))
# degree.t <- as.numeric(degree(graph.t))
# hist.t <- hist(degree.t, breaks=c(0:max(degree.t)), plot=F)

## SJTU
# fm.j <- read.csv('data/wifi_build_151214_fm_i24h', head=F, sep=',')
# colnames(fm.j) <- c('interval', 'from', 'from_lat', 'from_lon', 'to', 'to_lat', 'to_lon', 'unique', 'total')
# fm.j$interval = as.POSIXct(fm.j$interval * 3600 * 24, origin="1970-01-01 00:00:00", tz="Asia/Shanghai")

fm.j <- read.csv('data/wifi_ap_140914_fm_i24h', head=F, sep=',')
colnames(fm.j) <- c('interval', 'from', 'to', 'unique', 'total')
fm.j$interval = as.POSIXct(fm.j$interval * 3600 * 24, origin="1970-01-01 00:00:00", tz="Asia/Shanghai")

graph.j <- as.undirected(graph.data.frame(fm.j[, c("from", "to")]))
degree.j <- as.numeric(degree(graph.j))
hist.j <- hist(degree.j, breaks=c(0:max(degree.j)), plot=F)

############################
## Plot powerlaws
############################
pdf("figures/allthree_powerlaw.pdf", width=5, height=4)
par(mar=c(3.5, 3.5, 1, 1))
xlim=c(1, 200); ylim=c(10^-5, 0.7)
magplot(seq(1, 200, length.out = 10), log='xy', seq(ylim[1], ylim[2], length.out=10), type = "n",
        xlim=xlim, ylim=ylim, xlab="Degree of Vertex", ylab="PDF", side=1:4, labels=c(T,T,F,F))

cols = c('royalblue', 'orangered', 'slategray', 'sandybrown')

## Senegal
x = ceiling(hist.d$mids)
y = hist.d$density
points(x, y, log="xy", pch=0, cex=1, col=cols[1])
fit_truncated_power_law(x, y, xmax=80, col=cols[1], lty=1)

## Hangzhou
x = ceiling(hist.h$mids)
y = hist.h$density
points(x, y, log="xy", pch=6, cex=1, col=cols[2])
fit_truncated_power_law(x, y, xmax=25, col=cols[2], lty=2)

## Chicago
# x = ceiling(hist.t$mids)
# select=c(3:length(x))
# x = x[select]
# y = hist.t$density[select]
# points(x, y, log='xy', pch=21, cex=1, col=cols[3])
# fit_power_law(x, y, x0 = 13)

## SJTU
x = ceiling(hist.j$mids)
y = hist.j$density
points(x, y, log="xy", pch=20, cex=1, col=cols[4])
fit_truncated_power_law(x, y, xmax=70, col=cols[4], lty=5)

legend(1.5, 0.0005, legend=c("Country", "City", "Campus"), pch=c(0,6,20), col=cols)

dev.off()

