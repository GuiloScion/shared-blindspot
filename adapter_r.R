# adapter_r.R -- R's integrate(), the fifth implementation.
#
# R's integrate() wraps QUADPACK's dqags/dqagi in C translation, so it is NOT
# independent of scipy.integrate.quad. That is declared in SCOPE.md and is part
# of what this study measures: two routines that present as independent while
# sharing an algorithm.
#
# Writes CSV to stdout so run.py can fold it in with the Python adapters.

WIDTHS <- c(1e-1, 1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-8, 1e-10, 1e-12)
A <- -1.0; B <- 1.0
OFFSET <- 1.0 / 3.0

centre_of <- function(family) if (family == "centred") 0.0 else OFFSET

integrand <- function(family, w) {
  cc <- centre_of(family)
  function(x) {
    t <- (x - cc) / w
    out <- numeric(length(t))
    ok <- abs(t) <= 40
    out[ok] <- exp(-t[ok]^2)
    out
  }
}

cat("implementation,family,width,value,claimed,warned,error\n")
for (family in c("centred", "offcentre")) {
  for (w in WIDTHS) {
    f <- integrand(family, w)
    warned <- FALSE
    err <- ""
    val <- NA_real_
    claimed <- NA_real_
    res <- withCallingHandlers(
      tryCatch(integrate(f, A, B),
               error = function(e) { err <<- conditionMessage(e); NULL }),
      warning = function(cnd) { warned <<- TRUE; invokeRestart("muffleWarning") }
    )
    if (!is.null(res)) {
      val <- res$value
      claimed <- res$abs.error
      # integrate() signals trouble through $message rather than a warning
      if (!identical(res$message, "OK")) { warned <- TRUE; err <- res$message }
    }
    cat(sprintf("R integrate (QUADPACK),%s,%.17g,%.17g,%.17g,%s,%s\n",
                family, w, val, claimed, tolower(as.character(warned)), err))
  }
}
