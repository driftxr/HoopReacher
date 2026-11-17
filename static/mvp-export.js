const mvpExport = document.querySelector('[data-mvp-export]');
mvpExport.addEventListener('click', () => {
  const rows = Array.from(document.querySelector('#mvp-stats').rows, (row) =>
    Array.from(row.cells, (cell) => '"' + cell.textContent.trim().replaceAll('"', '""') + '"').join(',')
  );
  const url = URL.createObjectURL(new Blob(['\uFEFF', rows.join('\r\n')], { type: 'text/csv;charset=utf-8' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = mvpExport.dataset.mvpExport + '.csv';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
