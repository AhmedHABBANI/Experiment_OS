const API_PREFIX = "/api/v1";

async function postAnalysis(path, simulation, options, extraOptions = {}, includeTestOptions = true) {
  const response = await fetch(`${API_PREFIX}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      group_a: simulation.group_a,
      group_b: simulation.group_b,
      ...(includeTestOptions
        ? { alpha: options.alpha, alternative: options.alternative }
        : {}),
      ...extraOptions
    })
  });

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => null);
    const message = errorPayload?.error?.message ?? "The statistical analysis request failed.";
    throw new Error(message);
  }

  return response.json();
}

export function analyzeBinaryExperiment(simulation, options) {
  const path = options.test === "fisher-exact" ? "/analyses/fisher-exact" : "/analyses/two-proportion-z";
  return postAnalysis(path, simulation, options);
}

export function analyzeContinuousExperiment(simulation, options) {
  const paths = {
    "student-t": "/analyses/student-t",
    "welch-t": "/analyses/welch-t",
    "mann-whitney": "/analyses/mann-whitney",
    permutation: "/analyses/permutation",
    bootstrap: "/analyses/bootstrap-difference"
  };
  const path = paths[options.test] ?? paths["student-t"];
  let extraOptions = {};
  if (options.test === "permutation") {
    extraOptions = { n_permutations: options.n_permutations, seed: options.seed };
  } else if (options.test === "bootstrap") {
    extraOptions = {
      estimand: options.estimand,
      confidence_level: options.confidence_level,
      n_resamples: options.n_resamples,
      seed: options.seed
    };
  }
  return postAnalysis(path, simulation, options, extraOptions, options.test !== "bootstrap");
}
