# D99 (descripción de grupos): coordenadas de los contratos en el plano factorial del ACM de D98. Misma ACM, semilla y variables de
# patrones_hcpc_vtest.R; no se corre el HCPC y se verifica que los autovalores coincidan con hcpc_d98_inercia.csv.
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
guardado <- read.csv(file.path(dir_out, "hcpc_d98_inercia.csv"))
stopifnot(isTRUE(all.equal(unname(acm$eig[1:10, 2]), guardado$pct_varianza, tolerance = 1e-8)))
cat("autovalores idénticos a los de D98: sí\n")
write.csv(data.frame(dim1 = acm$ind$coord[, 1], dim2 = acm$ind$coord[, 2]), file.path(dir_out, "hcpc_d98_coordenadas.csv"), row.names = FALSE)
