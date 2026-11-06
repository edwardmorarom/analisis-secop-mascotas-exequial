# D106: partes en R de la validación de los grupos de HCPC. No cambia la partición de D98 (se verifica que se reproduce).
suppressMessages({library(FactoMineR); library(cluster)})
raiz <- normalizePath(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "..", ".."))
dir_out <- file.path(raiz, "data", "processed", "resultados_secop", "patrones")
b <- read.csv(file.path(raiz, "data", "processed", "resultados_secop", "patrones_base.csv"), stringsAsFactors = FALSE, colClasses = c(entidad_id = "character"))
comp <- c("inhumacion_cremacion", "traslado", "ataudes_bienes", "plan_exequial", "operacion_cementerio", "atencion_vulnerables_NN")
vars <- c("tipo_entidad", "modalidad_grupo", "tipo_contrato_hom", "orden_nivel", comp)
armar <- function(d) {
  x <- d[, vars]
  for (v in comp) x[[v]] <- factor(ifelse(x[[v]] == 1, paste0(v, "_si"), paste0(v, "_no")))
  for (v in setdiff(vars, comp)) x[[v]] <- factor(x[[v]])
  x
}
x <- armar(b)
d98 <- read.csv(file.path(dir_out, "hcpc_d98_grupos.csv"))$grupo
k98 <- length(unique(d98))

set.seed(2034)
acm <- MCA(x, ncp = 10, graph = FALSE)
hc <- HCPC(acm, nb.clust = -1, graph = FALSE)
stopifnot(identical(as.integer(hc$data.clust$clust), as.integer(d98)))
cat("clasificación idéntica a la de D98: sí (k =", k98, ")\n")

ganancia <- hc$call$t$inert.gain
write.csv(data.frame(de_k_a_k_mas_1 = seq_len(30), ganancia = head(ganancia, 30)), file.path(dir_out, "validacion_hcpc_ganancia_inercia.csv"), row.names = FALSE)

coord <- acm$ind$coord[, 1:10]
dc <- dist(coord)
sil <- do.call(rbind, lapply(4:12, function(k) {
  h <- HCPC(acm, nb.clust = k, graph = FALSE)
  cl <- as.integer(h$data.clust$clust)
  data.frame(k = k, silueta = mean(silhouette(cl, dc)[, "sil_width"]), grupo_mas_pequeno = min(tabulate(cl)))
}))
write.csv(sil, file.path(dir_out, "validacion_silueta.csv"), row.names = FALSE)
print(sil)

g <- daisy(x, metric = "gower")
p <- pam(g, k = k98, diss = TRUE)
write.csv(data.frame(grupo_pam = p$clustering), file.path(dir_out, "validacion_pam_gower.csv"), row.names = FALSE)
cat("PAM-Gower tamaños:", tabulate(p$clustering), "| silueta media:", p$silinfo$avg.width, "\n")

s2 <- which(b$fuente == "secop2")
x2 <- armar(b[s2, ])
for (v in names(x2)) x2[[v]] <- droplevels(x2[[v]])
set.seed(2034)
acm2 <- MCA(x2, ncp = 10, graph = FALSE)
auto <- HCPC(acm2, nb.clust = -1, graph = FALSE)
forz <- HCPC(acm2, nb.clust = k98, graph = FALSE)
write.csv(data.frame(fila = s2, grupo_auto = as.integer(auto$data.clust$clust), grupo_k11 = as.integer(forz$data.clust$clust)),
          file.path(dir_out, "validacion_secop2_grupos.csv"), row.names = FALSE)
cat("SECOP II: k automático =", length(unique(auto$data.clust$clust)), "| tamaños:", tabulate(as.integer(auto$data.clust$clust)), "\n")

xs <- cbind(x, fuente_sup = factor(b$fuente))
set.seed(2034)
acms <- MCA(xs, ncp = 10, quali.sup = ncol(xs), graph = FALSE)
hcs <- HCPC(acms, nb.clust = -1, graph = FALSE)
gs <- as.integer(hcs$data.clust$clust)
write.csv(data.frame(grupo_sup = gs), file.path(dir_out, "validacion_fuente_suplementaria.csv"), row.names = FALSE)
cd <- catdes(data.frame(clust = factor(gs), fuente = factor(b$fuente)), 1)
cat("fuente suplementaria: HCPC idéntico a D98:", identical(gs, as.integer(d98)), "\n")
