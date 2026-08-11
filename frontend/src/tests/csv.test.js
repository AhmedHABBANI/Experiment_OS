import { describe, expect, it } from "vitest";

import { simulationToCsv } from "../lib/csv.js";

describe("simulationToCsv", () => {
  it("serializes groups with blank cells for missing values", () => {
    const csv = simulationToCsv({
      group_a: [1, null, 0],
      group_b: [0.25, undefined]
    });

    expect(csv).toBe("row,group_a,group_b\n1,1,0.25\n2,,\n3,0,\n");
  });
});
