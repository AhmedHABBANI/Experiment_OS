import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import AnalysisResult from "../components/AnalysisResult.jsx";

afterEach(cleanup);

describe("AnalysisResult", () => {
  it("prioritizes the decision, interval and statistical cautions", () => {
    render(
      <AnalysisResult
        result={{
          test_name: "welch_t_test",
          statistic: 2.41,
          p_value: 0.017,
          alpha: 0.05,
          estimate: 1.84,
          effect_size: 0.28,
          effect_size_name: "cohens_d",
          reject_null: true,
          confidence_interval: { lower: 0.34, upper: 3.33, level: 0.95 },
          warnings: [
            {
              code: "SMALL_SAMPLE",
              message: "Interpret the estimate cautiously."
            }
          ],
          interpretation: {
            question: "Do the population means differ?",
            null_hypothesis: "The population means are equal.",
            alternative_hypothesis: "The population means differ.",
            decision: "The data provide sufficient evidence to reject H0.",
            effect: "The observed estimate is positive.",
            uncertainty: "The interval excludes zero."
          }
        }}
      />
    );

    expect(screen.getByRole("heading", { name: "Reject H0" })).toBeInTheDocument();
    expect(screen.getByText("alpha 0.0500")).toBeInTheDocument();
    expect(screen.getByText("[0.3400, 3.3300]")).toBeInTheDocument();
    expect(screen.getByText("SMALL SAMPLE")).toBeInTheDocument();
  });

  it("labels bootstrap results as estimation only", () => {
    render(
      <AnalysisResult
        result={{
          test_name: "bootstrap_mean_difference",
          statistic: null,
          p_value: null,
          estimate: 1.5,
          effect_size: null,
          effect_size_name: null,
          reject_null: null,
          confidence_interval: {
            lower: 0.2,
            upper: 2.8,
            level: 0.95
          },
          assumptions: [],
          warnings: [],
          interpretation: {
            question: "What is the mean difference?",
            null_hypothesis: "Not applicable.",
            alternative_hypothesis: "Not applicable.",
            decision: "No hypothesis-test decision is produced."
          }
        }}
      />
    );

    expect(screen.getByText("Estimation only")).toBeInTheDocument();
    expect(screen.queryByText("Do not reject H0")).not.toBeInTheDocument();
    expect(screen.getByText("Interval estimate")).toBeInTheDocument();
    expect(screen.getByText("95% confidence interval")).toBeInTheDocument();
  });
});
