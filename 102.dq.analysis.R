library(movr)
library(magicaxis)
library(Hmisc)
library(MASS)
library(plot3D)

hz.point <- readRDS('hz.dq.point.rds')
hz.traj <- readRDS('hz.dq.traj.rds')
sg.point <- readRDS('senegal.dq.point.rds')
sg.traj <- readRDS('senegal.dq.traj.rds')
sj.point <- readRDS('sjtu.dq.point.rds')
sj.traj <- readRDS('sjtu.dq.traj.rds')

cols = c('royalblue', 'orangered', 'slategray', 'sandybrown')

## Point quality (ECDF)
pdf('dq-point-ecdf.pdf', width=5, height=4.5)
par(mar=c(3, 3.5, 1, 1), mgp=c(2,0.5,0))
magplot(seq(0, 1, length.out = 10), type = "n", xlim=c(0,1), ylim=c(0,1),
        xlab=expression(Q[P]), ylab=expression(paste("ECDF ", Q[P])),
        side=1:4, labels=c(T,T,F,F))
Ecdf(sg.point$dq, what='1-F', col=cols[1], pch=0, add=TRUE, subtitles=F, lty=1)
Ecdf(hz.point$dq, what='1-F', col=cols[2], pch=6, add=TRUE, subtitles=F, lty=2)
Ecdf(sj.point$dq, what='1-F', col=cols[3], pch=20, add=TRUE, subtitles=F, lty=3)
legend(0.1, 0.4, c('Contury', 'City', 'Campus'), col=cols[1:3], lty=1:3)
dev.off()

## Trajetory quality (ECDF)
pdf('dq-traj-ecdf.pdf', width=5, height=4.5)
par(mar=c(3, 3.5, 1, 1), mgp=c(2,0.5,0))
magplot(seq(0, 1, length.out = 10), type = "n", xlim=c(0,1), ylim=c(0,1),
        xlab=expression(Q[I]), ylab=expression(paste("ECDF ", Q[I])),
        side=1:4, labels=c(T,T,F,F))
Ecdf(sg.traj$dq, what='1-F', col=cols[1], pch=0, add=TRUE, subtitles=F, lty=1)
Ecdf(hz.traj$dq, what='1-F', col=cols[2], pch=6, add=TRUE, subtitles=F, lty=2)
Ecdf(sj.traj$dq, what='1-F', col=cols[3], pch=20, add=TRUE, subtitles=F, lty=3)
legend(0.1, 0.4, c('Contury', 'City', 'Campus'), col=cols[1:3], lty=1:3)
dev.off()

## Trajectory entropy (ECDF)
pdf('dq-traj-entropy-ecdf.pdf', width=5, height=4.5)
par(mar=c(3, 3.5, 1, 1), mgp=c(2,0.5,0))
magplot(seq(0, 1, length.out = 10), type = "n", xlim=c(0,0.5), ylim=c(0,1),
        xlab=expression(paste("Entropy of ", Q[P])), ylab="ECDF (> E)",
        side=1:4, labels=c(T,T,F,F))
Ecdf(sg.traj$entropy, what='1-F', col=cols[1], pch=0, add=TRUE, subtitles=F, lty=1)
Ecdf(hz.traj$entropy, what='1-F', col=cols[2], pch=6, add=TRUE, subtitles=F, lty=2)
Ecdf(sj.traj$entropy, what='1-F', col=cols[3], pch=20, add=TRUE, subtitles=F, lty=3)
legend(0.3, 0.9, c('Contury', 'City', 'Campus'), col=cols[1:3], lty=1:3)
dev.off()

## dq.point vs dq.d
### Hangzhou
pdf('dq-vs-dq-d-hz.pdf', width=5, height=4.5)
par(mar=c(3, 3.5, 1, 1), mgp=c(2,0.5,0))
spl <- sample(1:nrow(hz.point), 200000)
magplot(hz.point[spl,]$dq, hz.point[spl,]$dq.d, pch='.',
        xlab=expression(Q[P]), ylab=expression(Q[a]), col=cols[1])
dev.off()

## dq.traj vs N
pdf('dq-traj-vs-N-hz.pdf', width=5, height=4.5)
par(mar=c(3, 3.5, 1, 1), mgp=c(2,0.5,0))
magplot(hz.traj$dq, hz.traj$N, pch='.', ylim=c(1,150),
        xlab=expression(Q[I]), ylab=expression(N))
dev.off()

## dq.traj vs entropy
pdf('dq-traj-vs-entropy-hz.pdf', width=5, height=4.5)
par(mar=c(3, 3.5, 1, 1), mgp=c(2,0.5,0))
magplot(hz.traj$dq, hz.traj$entropy, pch='.',
        xlab=expression(Q[I]), ylab=expression(paste("Entropy of ", Q[P])))
dev.off()

## Spatial distribution of Q[I]
dq.p <- hz.point
dq.t <- hz.traj

uinfo <- dq.p[,c('uid', 'stime', 'etime', 'x', 'y')] %>% as.data.frame
### find out HOME of each person
uhome <- uinfo %>% group_by(uid) %>% do({
  hours <- floor(.$stime/3600.0) : ceiling(.$etime/3600.0)
  tod <- as.numeric(hour2tod(hours, tz="Asia/Shanghai"))
  df <- data.frame(x=.$x, y=.$y, q=sum(tod %in% 0:7))
  df2 <- df %>% group_by(x, y) %>% summarise(q = sum(q))
  df2[order(-df2$q)[1], c('x', 'y')]
})

dq.spatial <- uhome %>% as.data.frame %>%
  inner_join(dq.t, by=c('uid'='uid')) %>%
  transmute(uid=uid, x=x, y=y, dq=dq)

# pdf('dq-spatial-dist-hz.pdf', width=5, height=5)
# wireframe(dq ~ x * y, data=dq.spatial, xlab="Longitude", ylab="Latitude",
#           drape=TRUE, colorkey=TRUE, screen = list(z = -60, x = -60))
# dev.off()
# 
# surf3D(dq.spatial$x, dq.spatial$y, dq.spatial$dq)
# 
# dq.mat <- vbin.grid(dq.spatial$x, dq.spatial$y, dq.spatial$dq, 500, 500, na=0)
# persp3D(dq.mat)
