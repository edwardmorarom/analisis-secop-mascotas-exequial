# D98: ACM + HCPC como descripción, con estabilidad por bootstrap (200 remuestreos, semilla 2034, Jaccard de Hennig 2007).
suppressMessages({library(FactoMineR); library(parallel)})
raiz <- normalizePath(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "..", ".."))
dir_res <- file.path(raiz, "data", "processed", "resultados_secop")
dir_out <- file.path(dir_res, "patrones")
b <- read.csv(file.path(dir_res, "patrones_base.csv"), stringsAsFactors = FALSE, colClasses = c(entidad_id = "character"))
comp <- c("inhumacion_cremacion", "traslado", "ataudes_bienes", "plan_exequial", "operacion_cementerio", "atencion_vulnerables_NN")
vars <- c("tipo_entidad", "modalidad_grupo", "tipo_contrato_hom", "orden_nivel", comp)
x <- b[, vars]
for (v in comp) x[[v]] <- factor(ifelse(x[[v]] == 1, paste0(v, "_si"), paste0(v, "_no")))
for (v in setdiff(vars, comp)) x[[v]] <- factor(x[[v]])

set.seed(2034)
acm <- MCA(x, ncp = 10, graph = FALSE)
hc <- HCPC(acm, nb.clust = -1, graph = FALSE)
k <- length(unique(hc$data.clust$clust))
orig <- as.integer(hc$data.clust$clust)
cat("grupos sugeridos por HCPC:", k, "| tamaños:", tabulate(orig), "\n")
write.csv(data.frame(grupo = orig), file.path(dir_out, "hcpc_d98_grupos.csv"), row.names = FALSE)
write.csv(data.frame(grupo = seq_len(k), contratos = tabulate(orig), pct = 100 * tabulate(orig) / length(orig)), file.path(dir_out, "hcpc_d98_tamanos.csv"), row.names = FALSE)
inercia <- data.frame(dimension = seq_len(nrow(acm$eig)), pct_varianza = acm$eig[, 2], pct_acumulado = acm$eig[, 3])
write.csv(head(inercia, 10), file.path(dir_out, "hcpc_d98_inercia.csv"), row.names = FALSE)

remuestreo <- function(r) {
  suppressMessages(library(FactoMineR))
  set.seed(2034 + r)
  idx <- sample.int(nrow(x), nrow(x), replace = TRUE)
  xb <- x[idx, ]
  for (v in names(xb)) xb[[v]] <- droplevels(xb[[v]])
  a <- tryCatch(MCA(xb, ncp = 10, graph = FALSE), error = function(e) NULL)
  if (is.null(a)) return(rep(NA_real_, k))
  h <- tryCatch(HCPC(a, nb.clust = k, graph = FALSE), error = function(e) NULL)
  if (is.null(h)) return(rep(NA_real_, k))
  cb <- as.integer(h$data.clust$clust)
  primero <- !duplicated(idx)
  u <- idx[primero]; cbu <- cb[primero]
  sapply(seq_len(k), function(i) {
    A <- u[orig[u] == i]
    if (length(A) == 0) return(NA_real_)
    max(sapply(seq_len(k), function(j) {B <- u[cbu == j]; length(intersect(A, B)) / length(union(A, B))}))
  })
}
cl <- makeCluster(min(10, detectCores() - 2))
clusterExport(cl, c("x", "orig", "k"))
jac <- parLapply(cl, 1:200, remuestreo)
stopCluster(cl)
J <- do.call(rbind, jac)
res <- data.frame(grupo = seq_len(k), contratos = tabulate(orig), jaccard_medio = colMeans(J, na.rm = TRUE),
                  jaccard_p05 = apply(J, 2, quantile, 0.05, na.rm = TRUE), pct_remuestreos_disueltos = 100 * colMeans(J < 0.5, na.rm = TRUE),
                  remuestreos_validos = colSums(!is.na(J)))
write.csv(res, file.path(dir_out, "hcpc_d98_estabilidad.csv"), row.names = FALSE)
print(res)
