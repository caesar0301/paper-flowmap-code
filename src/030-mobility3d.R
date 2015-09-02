## Hangzhou
library(plyr)
library(dplyr)
library(deldir)
library(magicaxis)
library(movr)
library(rgl)

mov <- readRDS("rdata/hcl.rds") %>% filter(uid <= 1000)
bm <- readRDS("rdata/hcl_bm.rds")
bm <- bm %>% filter(lon >= 120.0 & lon <= 120.5)

# calculate relative coordinates in KM
minlat <- min(bm$lat)
minlon <- min(bm$lon)
relxy <- function(lat, lon) {
  y = gcd(c(lat, minlon), c(minlat, minlon))
  x = gcd(c(minlat, lon), c(minlat, minlon))
  c(x, y)
}
bm <- ddply(bm, c("bid"), function(r) {
  r$x <- gcd(c(minlat, minlon), c(r$lat, minlon))
  r$y <- gcd(c(minlat, minlon), c(minlat, r$lon))
  r
})

# merge bm into mov data
mov <- left_join(mov, bm, by=c("bid"="bid"))

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# VISUALIZATION OF MOBILITY
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# plot 3D voronoi canvas
voronoi3d <- function(points, side, col.seg = "grey", col.point=col.seg, lty=1, lwd=1) {
  stopifnot(tolower(side) %in% c('x', 'y', 'z'))
  if (is.data.frame(points) || is.matrix(points))
    points = list(points)
  col.point = as.vector(col.point)
  if (length(col.point) == 1)
    col.point = rep(col.point, length(points))
  else
    stopifnot(length(col.point) == length(points))
  bbox = par3d('bbox')
  br = range(bbox)
  if (br[1] - br[2] > 3e+30)
    stop("A valid rgl canvas is needed first when calling voronoi3d{movr}.")
  xr = bbox[1:2]
  yr = bbox[3:4]
  zr = bbox[5:6]
  side = tolower(side)
  coord = cbind(xr, yr, zr)[,which(side == c('x', 'y', 'z'))]
  
  plot.direchlet.tess <- function() {
    points.all = do.call("rbind", points) %>% distinct_
    dd = deldir(points.all[,1], points.all[,2])
    dirsgs = dd$dirsgs
    p1 = as.vector(t(dirsgs[,c(1,3)]))
    p2 = as.vector(t(dirsgs[,c(2,4)]))
    p3 = rep(coord[1], 2)
    if (side == 'x') {
      x = p3
      y = p1
      z = p2
    } else if (side == 'y') {
      x = p1
      y = p3
      z = p2
    } else {
      x = p1
      y = p2
      z = p3
    }
    rgl.lines(x=x, y=y, z=z, lwd=lwd, lty=lty, color=col.seg)
  }
  plot.direchlet.tess()
  
  plot.points <- function(points, col) {
    points = as.data.frame(points) %>% distinct_
    s1 = as.vector(points[,1])
    s2 = as.vector(points[,2])
    s3 = rep(coord[1], 2)
    if (side == 'x') {
      px = s3
      py = s1
      pz = s2
    } else if (side == 'y') {
      px = s1
      py = s3
      pz = s2
    } else {
      px = s1
      py = s2
      pz = s3
    }
    rgl.points(x=px, y=py, z=pz, color=col, alpha=0.5)
  }
  
  for ( i in 1:length(points)) {
    plot.points(points[i], col.point[i])
  }
}

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# select one user
user <- mov %>% filter(uid == 1 & time - min(time) <= 86600 * 30)
user2 <- mov %>% filter(uid == 12 & time - min(time) <= 86600 * 30)
user3 <- mov %>% filter(uid == 1 & time - min(time) <= 86600 * 30)
#++++++++++++++++++++++++++++++++++++++
par3d(windowRect=c(20,40,800,800))
rgl.clear()
rgl.clear("lights")
rgl.bg(color="white")
rgl.viewpoint(theta = 65, phi = 15)
rgl.light(theta = 45, phi = 45, viewpoint.rel=TRUE)

mobility3d <- function(x, y, t, size=2.5, col=colors()[sample(1:255,1)],
                         xlab="", ylab="", zlab="", add=FALSE, ...) {
  plot3d(x, t, y, type='p', size=2.5, col=col, xlab=xlab, ylab=ylab, zlab=zlab, add=add, ...)
  lines3d(x, t, y, color=col, ...)
}

col1 = colors()[136]
col2 = colors()[122]
col3 = colors()[51]
mobility3d(user$x, user$y, user$t-min(user$t), col=col1)
mobility3d(user2$x, user2$y, user2$t-min(user2$t), col=col2, add=T)
mobility3d(user3$x, user3$y, user3$t-min(user3$t), col=col3, add=T)

points = list(user[, c('x', 'y')] %>% distinct,
              user2[, c('x', 'y')] %>% distinct,
              user3[, c('x', 'y')] %>% distinct)
voronoi3d(points, side='y')

title3d(xlab="East-West (km)", ylab="Time", zlab="North-South (km)")
axes3d(lwd=0.7, xlen=8, ylen=10, zlen=8, col='black', marklen=40)
grid3d(side=c("x", "z"), lwd=0.7, lty=2)

for(i in seq(65, 360+65, by = 0.15)) {
  rgl.viewpoint(theta = -90+i, phi =30)
}

rgl.postscript("figures/mobility3d.pdf", fmt="pdf")
rgl.close()
