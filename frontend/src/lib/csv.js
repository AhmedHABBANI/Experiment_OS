export function simulationToCsv(result) {
  const maxRows = Math.max(result.group_a.length, result.group_b.length);
  const rows = ["row,group_a,group_b"];

  for (let index = 0; index < maxRows; index += 1) {
    rows.push(
      [
        index + 1,
        formatCsvValue(result.group_a[index]),
        formatCsvValue(result.group_b[index])
      ].join(",")
    );
  }

  return `${rows.join("\n")}\n`;
}

export function downloadCsv(filename, csvContent) {
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function formatCsvValue(value) {
  return value === null || value === undefined ? "" : String(value);
}
