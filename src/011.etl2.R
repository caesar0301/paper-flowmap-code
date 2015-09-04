# Script to convert csv files into rds.
library(data.table)

# HZ data
movement <- fread("data/hcl.dat", sep=",", head=F)
setnames(movement, c("uid", "time", "bid"))
saveRDS(as.data.frame(movement), file="rdata/hcl.rds")

bsmap <- fread("data/hcl_bm.dat", sep=",", head=F,
               colClasses=c("integer", "character", "numeric", "numeric"))
setnames(bsmap, c("bid", "bs", "lon", "lat"))
bsmap <- bsmap %>% filter(lon >= 120.0 & lon <= 120.5)
saveRDS(as.data.frame(bsmap), file="rdata/hcl_bm.rds")

# D4D Senegal data
users_arr <- fread("data/dap01cl.dat", sep=",", head=F)
setnames(users_arr, c("usr", "time", "arr"))
saveRDS(as.data.frame(users_arr), "rdata/dap01cl.rds")

users_site <- fread("data/dsp10cl.dat", sep=",",head=F)
setnames(users_site, c("usr", "time", "site"))
saveRDS(as.data.frame(users_site), "rdata/dsp10cl.rds")