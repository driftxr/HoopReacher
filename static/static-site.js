// All data is already in the HTML. No API or localhost requests are made.
(() => {
  const query = new URLSearchParams(location.search);
  const base = query.get('back') === 'standings' ? 'standings' : 'home';
  if (document.body.dataset.page === 'team') {
    const back = document.querySelector('.back-link');
    if (back) { back.href = base === 'standings' ? 'standings.html' : 'index.html'; back.textContent = '← Back to ' + (base === 'standings' ? 'Standings' : 'Picks'); }
    document.querySelectorAll('.team-switch a').forEach(a => { const url = new URL(a.href); url.searchParams.set('back', base); a.href = url.href; });
  }
  document.querySelectorAll('table').forEach(table => {
    table.querySelectorAll('.static-sort').forEach(button => button.addEventListener('click', () => {
      const th = button.closest('th');
      const direction = th.getAttribute('aria-sort') === 'ascending' ? 'desc' : th.getAttribute('aria-sort') === 'descending' ? 'asc' : button.dataset.default;
      const column = Number(button.dataset.column);
      const value = row => {
        const text = row.cells[column]?.textContent.trim() ?? '';
        if (!text || text === '—' || text === '—–—') return null;
        if (text === 'Match') return 0;
        if (/^\d+[–-]\d+$/.test(text)) { const [w,l] = text.split(/[–-]/).map(Number); return w * 1000 - l; }
        if (/^[+-]?\d+(\.\d+)?%?$/.test(text)) return parseFloat(text);
        return text.toLocaleLowerCase();
      };
      const rows = Array.from(table.tBodies[0].rows);
      rows.sort((a,b) => { const av=value(a),bv=value(b); if(av===null||bv===null)return av===null?(bv===null?0:1):-1; return (typeof av==='number' && typeof bv==='number'?av-bv:String(av).localeCompare(String(bv)))*(direction==='asc'?1:-1); });
      rows.forEach(row => table.tBodies[0].append(row));
      table.querySelectorAll('th').forEach(header => { header.setAttribute('aria-sort','none'); const icon=header.querySelector('span[aria-hidden]'); if(icon)icon.textContent='↕'; });
      th.setAttribute('aria-sort',direction==='asc'?'ascending':'descending');const icon=button.querySelector('span');if(icon)icon.textContent=direction==='asc'?'↑':'↓';
    }));
  });
  const date = document.querySelector('input[type="date"]');
  if (date) {
    const parts = new Intl.DateTimeFormat('en-US',{timeZone:'America/Toronto',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
    const part = type => parts.find(p=>p.type===type).value;
    const requested=query.get('date');date.value=/^\d{4}-\d{2}-\d{2}$/.test(requested||'')?requested:`${part('year')}-${part('month')}-${part('day')}`;
  }
  const filter = document.querySelector('select[name="filter"]');
  if(filter && ['all','upcoming','completed'].includes(query.get('filter')))filter.value=query.get('filter');
  const applyFilter = () => {
    const rows = Array.from(document.querySelectorAll('tr[data-date],tr[data-status]'));
    rows.forEach(row => { row.hidden = Boolean((date && row.dataset.date!==date.value) || (filter && filter.value==='completed' && row.dataset.status!=='3') || (filter && filter.value==='upcoming' && row.dataset.status==='3')); });
    let empty=document.getElementById('static-empty');
    if(!empty && rows.length){empty=document.createElement('p');empty.id='static-empty';empty.className='status';empty.textContent='No games available for this view.';document.querySelector('.table-wrap').after(empty);}
    if(empty)empty.hidden=rows.some(row=>!row.hidden);
  };
  if(date || filter){document.querySelectorAll('form').forEach(form=>form.addEventListener('submit',event=>{event.preventDefault();applyFilter();}));applyFilter();}
})();

// Standings use the same joined conference tabs as the picks homepage.
(() => {
  if(document.body.dataset.page !== 'standings') return;
  const root=document.querySelector('.conferences');
  if(!root) return;
  const panels=[...root.querySelectorAll('[data-conference]')];
  if(panels.length!==2) return;
  const tabs=document.createElement('div');
  tabs.className='standings-tabs';tabs.setAttribute('role','tablist');tabs.setAttribute('aria-label','Choose conference');
  const buttons=[];
  const activate=(index,focus=false)=>{
    buttons.forEach((button,i)=>{
      button.setAttribute('aria-selected',String(i===index));button.tabIndex=i===index?0:-1;panels[i].hidden=i!==index;
    });
    if(focus) buttons[index].focus();
  };
  panels.forEach((panel,index)=>{
    const conf=panel.dataset.conference;
    const button=document.createElement('button');button.type='button';button.textContent=conf+'ern Conference';button.id='standings-tab-'+conf;
    panel.id='standings-panel-'+conf;panel.setAttribute('role','tabpanel');panel.setAttribute('aria-labelledby',button.id);
    button.setAttribute('role','tab');button.setAttribute('aria-controls',panel.id);
    button.addEventListener('click',()=>activate(index));
    button.addEventListener('keydown',event=>{
      if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
      event.preventDefault();activate(event.key==='Home'?0:event.key==='End'?1:1-index,true);
    });
    buttons.push(button);tabs.append(button);
  });
  root.prepend(tabs);activate(0);
})();
