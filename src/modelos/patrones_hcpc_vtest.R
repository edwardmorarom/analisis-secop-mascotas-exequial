# D99 (enmienda): categorías características de cada grupo de HCPC (prueba v de FactoMineR), con la misma ACM, semilla y variables de patrones_hcpc_bootstrap.R.
suppressMessages(library(FactoMineR))
raiz <- normalizePath(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "..", ".."))
dir_out <- file.path(raiz, "data", "processed", "resultados_secop", "patrones")
b <- read.csv(file.path(raiz, "data", "processed", "resultados_secop", "patrones_base.csv"), stringsAsFactors = FALSE, colClasses = c(entidad_id = "character"))
comp <- c("inhumacion_cremacion", "traslado", "ataudes_bienes", "plan_exequial", "operacion_cementerio", "atencion_vulnerables_NN")
vars <- c("tipo_entidad", "modalidad_grupo", "tipo_contrato_hom", "orden_nivel", comp)
x <- b[, vars]
for (v in comp) x[[v]] <- factor(ifelse(x[[v]] == 1, paste0(v, "_si"), paste0(v, "_no")))
for (v in setdiff(vars, comp)) x[[v]] <- factor(x[[v]])
set.seed(2034)
acm <- MCA(x, ncp = 10, graph = FALSE)
hc <- HCPC(acm, nb.clust = -1, graph = FALSE)
orig <- as.integer(hc$data.clust$clust)
guardado <- read.csv(file.path(dir_out, "hcpc_d98_grupos.csv"))$grupo
stopifnot(identical(orig, as.integer(guardado)))
cat("clasificación idéntica a la de D98: sí\n")
filas <- list()
for (g in seq_along(hc$desc.var$category)) {
  cg <- hc$desc.var$category[[g]]
  if (is.null(cg)) next
  filas[[length(filas) + 1]] <- data.frame(grupo = g, categoria = rownames(cg), pct_de_la_categoria_en_el_grupo = cg[, "Cla/Mod"], pct_del_grupo_en_la_categoria = cg[, "Mod/Cla"],
                                           pct_global = cg[, "Global"], v_test = cg[, "v.test"], p = cg[, "p.value"])
}
write.csv(do.call(rbind, filas), file.path(dir_out, "hcpc_d98_vtest.csv"), row.names = FALSE, fileEncoding = "UTF-8")
