## Visualize flowmap in an elegant way with movr::draw_flowmap()
## Xiaming
library(dplyr)
library(movr)
library(geosphere)

jpeg('figures/allthree_fm.jpg', width=16000, height=4500)
par(mfrow=c(1,3), bg='black', mar=c(5,5,25,5))

#######################
## Senegal
#######################
locmap <- read.csv('data/SITE_ARR_LONLAT.CSV', head=T, sep=',')
dat <- read.csv('data/scl_fine_p06_fm_i24h', head=F, sep=',')
colnames(dat) <- c("interval", "from", "to", "unique", "total")

dat2 <- dat %>% left_join(locmap, by=c('from' = 'site_id')) %>%
  select(-arr_id, from_lon=lon, from_lat=lat) %>%
  left_join(locmap, by=c('to' = 'site_id')) %>%
  select(-arr_id, to_lon=lon, to_lat=lat)

#jpeg('figures/scl_fine_p06_fm_i24h.jpg', width=6800, height=4800)
dat3 <- dat2[sample(1:nrow(dat2), 600000, replace=F),]
draw_flowmap(dat3$from_lat, dat3$from_lon, dat3$to_lat, dat3$to_lon,
             main="Senegal, Africa", col.main='Green', cex.main=20)
#dev.off()

#######################
## HzMobile
#######################
bsmap <- read.csv('data/hcl_mesos0825_bm', head=F, sep=',')
colnames(bsmap) <- c('bid', 'lacid', 'lon', 'lat')
dat <- read.csv('data/hcl_mesos0825_fm_i6h', head=F, sep=',')
colnames(dat) <- c("interval", "from", "to", "unique", "total")

dat2 <- dat %>% dplyr::filter(interval == 62309) %>%
  left_join(bsmap, by=c('from' = 'bid')) %>%
  select(-lacid, from_lon=lon, from_lat=lat) %>%
  left_join(bsmap, by=c('to' = 'bid')) %>%
  select(-lacid, to_lon=lon, to_lat=lat) %>%
  dplyr::filter(unique>=3)

#jpeg('figures/hcl_mesos0825_fm_i6h.jpg', width=6400, height=4800)
draw_flowmap(dat2$from_lat, dat2$from_lon, dat2$to_lat, dat2$to_lon,
             main="HangZhou, China", col.main='Green', cex.main=20)
#dev.off()

#######################
## Wifi
#######################
dat <- read.table('data/wifi_151214_fm_i24h', head=F, sep=',', stringsAsFactors=F)
colnames(dat) <- c('interval', 'from_name', 'from_lat', 'from_lon', 'to_name', 'to_lat', 'to_lon', 'unique', 'total')
dat <- dat[complete.cases(dat),]

sjtu_campus <- c(121.429785,31.020148,121.46349,31.04583)
dat2 <- dat %>%
  mutate(from_lat = as.numeric(from_lat),
         from_lon = as.numeric(from_lon),
         to_lat = as.numeric(to_lat),
         to_lon = as.numeric(to_lon)) %>%
  dplyr::filter(from_lat != to_lat | from_lon != to_lon) %>%
  dplyr::filter(in_area(from_lon, from_lat, sjtu_campus) & in_area(to_lon, to_lat, sjtu_campus))

# library(shp2graph)
# rn<-readShapeLines("data/wifi_campus_shapefile/roads_clean.shp", proj4string=CRS(as.character(NA)))
# res<-nt.connect(rn) # the largest connected part

#jpeg('figures/wifi_151214_fm_i24h.jpg', width=6400, height=4800)
draw_flowmap(dat2$from_lat, dat2$from_lon, dat2$to_lat, dat2$to_lon,
             weight = dat2$total, weight.log = TRUE,
             main="SJTU, Shanghai", col.main='Green', cex.main=20)
dev.off()
