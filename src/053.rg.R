library(magicaxis)

rgweek <- read.csv('data/hcl_mesos0822_rg', sep=',', head=F)
colnames(rgweek) <- c('uid', 'rg')
rgwend <- read.csv('data/hcl_mesos0825_rg', sep=',', head=F)
colnames(rgwend) <- c('uid', 'rg')


plot_rg_fitted <- function(dens, ...) {
  # Fit density distribution with exp(ax^2+bx+c) * x^d model
  magplot(dens$x, dens$p, xlab = 'Radius of gyration (km)', ylab='Probabiilty', ...)
  lm.out <- lm(log(dens$p) ~ dens$x + I(dens$x ^ 2) + I(log(dens$x)))
  curve(exp(lm.out$coefficients[1] + lm.out$coefficients[2]* x + lm.out$coefficients[3]* x^2) * x^lm.out$coefficients[4],
        add=T, lwd=2)
  text(7, 0.15, substitute(paste(p, ' ~ ', e ^ {a + b*x + c*x^2}, x^{d}, sep=''),
                           list(a=format(lm.out$coefficients[1], digits=3),
                                b=format(lm.out$coefficients[2], digits=3),
                                c=format(lm.out$coefficients[3], digits=3),
                                d=format(lm.out$coefficients[4], digits=3))))
}

filter_rg_data <- function(v) {
  rg_hist <- hist(v, breaks=80, plot=F)
  N = length(rg_hist$breaks)
  rg_dens <- data.frame(x = 0.5*(rg_hist$breaks[1:N-1] + rg_hist$breaks[2:N]), p = rg_hist$density)
  rg_dens$p[rg_dens$p==0] <- 1e-6
  rg_dens <- rg_dens %>% dplyr::filter(x>0.2)
  rg_dens
}

svg('figures/hcl_mesos_rg.svg', height=5, width=5)
par(mfrow=c(2,1), mar=c(3.5,3.5,1,1), mgp=c(2,1,0))

rg_dens <- filter_rg_data(rgweek$rg)
plot_rg_fitted(rg_dens, col='orangered', pch=20)

rg_dens <- filter_rg_data(rgwend$rg)
plot_rg_fitted(rg_dens, col='royalblue', pch=20)

dev.off()


################################################
#  RG  with travelling distance distribution
################################################

pdf('figures/hcl_mesos_trvd.pdf', height=4, width=4)

trd[sample(1:nrow(trd), 1000), ]

trddat <- read.csv('data/mesos0825_s0dot2/mesos0825_s0dot2_trd', sep=',', head=T)
trd <- trddat[sample(1:nrow(trd), 5000), ]
magplot(trd$rg, trd$trvd, col=colors()[327], log='xy', side=1:4, labels=c(T,T,F,F),
        xlab="Radius of Gyration (km)", ylab="Travelling Distance (km)")
x = log(trd$rg)
y = log(trd$trvd)

lm.out <- lm(log(y) ~ log(x))
cc <- coef(lm.out)
curve(x^cc[2] * exp(cc[1]), add=T, lwd=2, col='orangered')
text(0.01, 100, substitute(paste(Y, ' ~ ', L * r[g] ^ {a}, sep=''),
                            list(a = format(cc[2], digits=3),
                                 L=format(exp(cc[1]), digits=3))))

dev.off()