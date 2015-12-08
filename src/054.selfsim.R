################################################
#  Self similarity vs. cluster distance
################################################
library(magicaxis)
library(dplyr)

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

## Parameters specific for mesos0825_sdot2
dat <- read.csv('data/mesos0825_s0dot2/mesos0825_s0dot2_trd', head=T, sep=',')
right <- dat %>%
  dplyr::filter(selfdist < -0.12 + 1.22 * dist
                & dist > 0.54 & selfdist > 0, selfdist < 1
                & selfdist > -1.15 + 2 * dist)
left <- dat %>% dplyr::filter(group==2 & selfdist > 0)
bottom <- dat %>% dplyr::filter(selfdist == 0)
others <- dat %>% dplyr::filter(group != 2 & selfdist != 0 & !(
  (selfdist %in% c(right$selfdist)) + (dist %in% c(right$dist)) == 2))

# do potting
svg('figures/mesos0825_s0dot2_selfsim.svg', width=6, height=4)
par(mar=c(4,4,1,1), mgp=c(1,0.5,0), cex.lab=1.5, cex=0.6)
magplot(others$dist, others$selfdist, pch=16, col=colors()[222], xlab="Distance",
        ylab="1 - SelfSim", xlim=c(0,1), ylim=c(0,1))

# add right points
right_sample <- right[sample(1:nrow(right), 5000, replace=F), ] # to make efficient plotting
points(right_sample$dist, right_sample$selfdist, col='royalblue', pch=16)
lm.out <- lm(right_sample$selfdist ~ right_sample$dist)
cc <- coef(lm.out)
curve( cc[1] + cc[2] * x, add=T, xlim=c(0.5, 1), lwd=2)
text(0.8, 0.2, substitute(paste('y ~ ', a, ' + ', b, 'x'),
                          list( a = format(cc[1], digits = 3),
                                b = format(cc[2], digits = 3))), cex=2)
arrows(0.73,0.25, 0.65, 0.5)

# add left points
points(left$dist, left$selfdist, col='orangered', pch=16)
left_log <- left %>% dplyr::filter(selfdist > 0 & dist > 0 & !(dist > 0.38 & selfdist < 0.62))
lm.out <- lm(left_log$selfdist ~ log(left_log$dist))
cc <- coef(lm.out)
curve( cc[1] + cc[2] * log(x), add=T, xlim=c(0.05, 0.7), lwd=2)
text(0.25, 0.8,
     substitute(paste('y ~ ', a, '  + ', b, log, 'x'),
                list( a = format(cc[1], digits = 3),
                      b = format(cc[2], digits = 3))), cex = 2)
arrows(0.3,0.75, 0.35, 0.7)

# add bottom points
bottom_sample <- bottom[sample(1:nrow(right), 500, replace=F), ]
points(bottom_sample$dist, bottom_sample$selfdist, pch=16, col=colors()[499])
dev.off()

# print percentage
print(paste("bottom: ", nrow(bottom) / nrow(dat)))
print(paste("left: ", nrow(left) / nrow(dat)))
print(paste("right: ", nrow(right) / nrow(dat)))
