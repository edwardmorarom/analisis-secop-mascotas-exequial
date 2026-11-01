# D98: clases latentes con poLCA (100 arranques, 2 a 10 clases, tres modelos), sin cuartil del valor; residuo bivariado de D97.
suppressMessages({library(poLCA); library(parallel)})
raiz <- normalizePath(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), "..", ".."))
dir_res <- file.path(raiz, "data", "processed", "resultados_secop")
dir_out <- file.path(dir_res, "patrones")
dir.create(dir_out, showWarnings = FALSE, recursive = TRUE)

b <- read.csv(file.path(dir_res, "patrones_base.csv"), stringsAsFactors = FALSE, colClasses = c(entidad_id = "character"))
items <- c("tipo_entidad", "modalidad_grupo", "tipo_contrato_hom", "orden_nivel",
           "inhumacion_cremacion", "traslado", "ataudes_bienes", "plan_exequial", "operacion_cementerio", "atencion_vulnerables_NN")
d <- data.frame(lapply(b[items], function(x) as.integer(factor(x))))
d$fuente <- as.integer(b$fuente == "secop2")
d$anio <- factor(b$anio)
n <- nrow(d)
niveles <- sapply(d[items], max)
rhs <- c("1", "fuente", "fuente + anio")
modelos <- c("sin covariables", "fuente", "fuente y año")
ARRANQUES <- 100

bvr_pares <- function(fit) {
  K <- length(fit$P)
  prior <- if (is.matrix(fit$prior) && nrow(fit$prior) == n) fit$prior else matrix(fit$P, n, K, byrow = TRUE)
  pk <- colSums(prior)
  out <- list()
  for (i in 1:(length(items) - 1)) for (j in (i + 1):length(items)) {
    O <- table(factor(d[[items[i]]], 1:niveles[i]), factor(d[[items[j]]], 1:niveles[j]))
    E <- Reduce(`+`, lapply(1:K, function(k) outer(fit$probs[[i]][k, ], fit$probs[[j]][k, ]) * pk[k]))
    m <- E > 1e-9
    gl <- (niveles[i] - 1) * (niveles[j] - 1)
    out[[length(out) + 1]] <- data.frame(var1 = items[i], var2 = items[j], bvr = sum(((O - E)^2)[m] / E[m]) / max(gl, 1))
  }
  o <- do.call(rbind, out)
  o[order(-o$bvr), ]
}

tarea <- function(t) tryCatch(tarea0(t), error = function(e) {message("tarea ", t$m, "/", t$K, ": ", conditionMessage(e)); NULL})
tarea0 <- function(t) {
  m <- t$m; K <- t$K
  f <- as.formula(paste0("cbind(", paste(items, collapse = ","), ") ~ ", rhs[m]))
  lls <- rep(NA_real_, ARRANQUES); mejor <- NULL
  for (a in 1:ARRANQUES) {
    set.seed(2034 + a + 1000 * K + 100000 * m)
    fit <- tryCatch(suppressMessages(poLCA(f, d, nclass = K, nrep = 1, maxiter = 2000, tol = 1e-10, verbose = FALSE, calc.se = FALSE)), error = function(e) NULL)
    if (is.null(fit)) next
    lls[a] <- fit$llik
    if (is.null(mejor) || fit$llik > mejor$llik) mejor <- fit
  }
  if (is.null(mejor)) return(NULL)
  bv <- bvr_pares(mejor)
  tam <- tabulate(mejor$predclass, K)
  post <- mejor$posterior
  ent <- 1 - (-sum(post * log(pmax(post, 1e-300)))) / (n * log(K))
  fila <- data.frame(modelo = m, covariables = modelos[m], clases = K, parametros = mejor$npar, logLik = mejor$llik,
                     BIC = -2 * mejor$llik + mejor$npar * log(n), AIC = -2 * mejor$llik + 2 * mejor$npar, entropia_relativa = ent,
                     arranques_con_el_maximo = sum(abs(lls - mejor$llik) < 1e-3, na.rm = TRUE), arranques_validos = sum(!is.na(lls)),
                     tamano_minimo_pct = 100 * min(tam) / n, bvr_maximo = bv$bvr[1], pares_bvr_mayor_10 = sum(bv$bvr > 10),
                     tamanos = paste(tam, collapse = " "))
  list(fila = fila, bvr = bv, fit = mejor[c("probs", "P", "prior", "predclass", "llik", "npar")])
}

if (Sys.getenv("PRUEBA") == "1") {ARRANQUES <- 3; r <- tarea0(list(m = 3, K = 3)); print(r$fila); print(head(r$bvr, 3)); quit()}
tareas <- expand.grid(m = 1:3, K = 2:10)
tareas <- lapply(seq_len(nrow(tareas)), function(i) list(m = tareas$m[i], K = tareas$K[i]))
tareas <- tareas[order(-sapply(tareas, function(t) t$K * (1 + t$m)))]
cl <- makeCluster(min(10, detectCores() - 2))
clusterExport(cl, c("items", "d", "n", "niveles", "rhs", "modelos", "ARRANQUES", "bvr_pares", "tarea", "tarea0"))
clusterEvalQ(cl, suppressMessages(library(poLCA)))
res <- parLapply(cl, tareas, tarea)
stopCluster(cl)
res <- res[!sapply(res, is.null)]
tabla <- do.call(rbind, lapply(res, `[[`, "fila"))
tabla <- tabla[order(tabla$modelo, tabla$clases), ]
tabla$dBIC <- tabla$BIC - min(tabla$BIC)
write.csv(tabla, file.path(dir_out, "polca_comparacion.csv"), row.names = FALSE, fileEncoding = "UTF-8")
saveRDS(res, file.path(dir_out, "polca_ajustes.rds"))
print(tabla[, c("covariables", "clases", "parametros", "BIC", "dBIC", "arranques_con_el_maximo", "tamano_minimo_pct", "bvr_maximo", "pares_bvr_mayor_10")], digits = 4, row.names = FALSE)
