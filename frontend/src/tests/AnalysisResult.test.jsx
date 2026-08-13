import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import AnalysisResult from "../components/AnalysisResult.jsx";

describe("AnalysisResult", () => {
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
  });
});
