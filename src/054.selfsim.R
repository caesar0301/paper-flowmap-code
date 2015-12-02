################################################
#  Self similarity vs. cluster distance
################################################
library(magicaxis)

# Unsed, for backup
cut_with_mids <- function(x, breaks) {
  # cut vector to bins and return mid points
  r <- range(x)
  b <- seq(r[1], r[2], length=2*breaks+1)
  brk <- b[0:breaks*2+1]
  mid <- b[1:breaks*2]
  brk[1] <- brk[1]-0.01
  k <- cut(x, breaks=brk, labels=FALSE)
  mid[k]
}

svg('figures/mesos0825_s0dot2_selfsim.svg', width=6, height=4)
par(mar=c(4,4,1,1), mgp=c(1,0.5,0), cex.lab=1.5)

dat <- read.csv('data/mesos0825_s0dot2/mesos0825_s0dot2_trd', head=T, sep=',')
magplot(dat$dist, dat$selfdist, pch=16, col=colors()[222], xlab="Distance",
        ylab="1 - SelfSim", xlim=c(0,1), ylim=c(0,1))

right <- dat %>% dplyr::filter(selfdist < -0.12 + 1.22 * dist & dist > 0.54 & selfdist > 0, selfdist < 1)

left <- dat %>% dplyr::filter(selfdist > 0.93 + 0.36 * log(dist) & dist <= 0.5 & selfdist > 0 & selfdist < 1)
left <- left %>% dplyr::filter(!(dist > 0.3 & selfdist < 0.625))
left <- left %>% dplyr::filter(!(dist > 0.16 & selfdist < 0.4))
left <- left %>% dplyr::filter(selfdist>0.05)

top <- dat %>% dplyr::filter(selfdist == 1)
bottom <- dat %>% dplyr::filter(selfdist == 0)

others <- dat %>% dplyr::filter(!(
  (selfdist %in% c(right$selfdist, left$selfdist, top$selfdist, bottom$selfdist)) +
    (dist %in% c(right$dist, left$dist, top$selfdist, bottom$selfdist)) == 2))

# do potting
magplot(others$dist, others$selfdist, pch=16, col=colors()[222], xlab="Distance",
        ylab="1 - SelfSim", xlim=c(0,1), ylim=c(0,1))
text()

# add right points
right_sample <- right[sample(1:nrow(right), 2000, replace=F), ] # to make efficient plotting
points(right_sample$dist, right_sample$selfdist, col='royalblue', pch=16)
lm.out <- lm(right$selfdist ~ right$dist)
cc <- coef(lm.out)
curve( cc[1] + cc[2] * x, add=T, xlim=c(0.5, 1), lwd=2)
text(0.8, 0.2, substitute(paste('y ~ ', a, ' + ', b, 'x'),
                          list( a = format(cc[1], digits = 3),
                                b = format(cc[2], digits = 3))))
arrows(0.73,0.25, 0.65, 0.5)

# add left points
points(left$dist, left$selfdist, col='orangered', pch=16)
lm.out <- lm(left$selfdist ~ log(left$dist))
cc <- coef(lm.out)
curve( cc[1] + cc[2] * log(x), add=T, xlim=c(0, 0.5), lwd=2)
text(0.25, 0.8, substitute(paste('y ~ ', a, '  + ', b, log, 'x'),
                           list( a = format(cc[1], digits = 3),
                                 b = format(cc[2], digits = 3))))
arrows(0.3,0.75, 0.35, 0.7)

# add top points
points(top$dist, top$selfdist, pch=16, col=colors()[222])

# add bottom points
bottom_sample <- bottom[sample(1:nrow(right), 500, replace=F), ]
points(bottom_sample$dist, bottom_sample$selfdist, pch=16, col=colors()[222])

# print percentage
print(paste("bottom: ", nrow(bottom) / nrow(dat)))
print(paste("top: ", nrow(top) / nrow(dat)))
print(paste("left: ", (nrow(left) + nrow(dat %>% dplyr::filter(selfdist < 0.04 & selfdist > 0))) / nrow(dat)))
print(paste("right: ", (nrow(right) - nrow(right %>% dplyr::filter(selfdist == 0))) / nrow(dat)))

dev.off()
