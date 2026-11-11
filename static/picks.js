(() => {
  const node=document.getElementById('picks-data');if(!node)return;
  const data=JSON.parse(node.textContent),season=data.season,key='hoopreacher:picks:v1:'+season;
  const teams=data.teams,byId=new Map(teams.map(t=>[t.TeamID,t]));
  const blank=()=>({East:Array(10).fill(null),West:Array(10).fill(null)});
  let picks=blank(),saved=false,activeConference='East';
  const status=document.getElementById('pick-status');
  const tell=text=>status.textContent=text;
  function validate(doc){
    if(!doc||doc.format!=='hoopreacher-picks'||doc.version!==1||doc.season!==season)throw Error('Choose a HoopReacher picks file for '+season+'.');
    const clean=blank();
    for(const conf of ['East','West']){
      const rows=doc.picks?.[conf];if(!Array.isArray(rows)||rows.length!==10)throw Error('Each conference must contain 10 slots.');
      const used=new Set();rows.forEach((id,i)=>{if(id===null)return;if(!Number.isInteger(id)||byId.get(id)?.Conference!==conf||used.has(id))throw Error('The file contains an invalid team or duplicate pick.');used.add(id);clean[conf][i]=id;});
    }return clean;
  }
  const documentData=()=>({format:'hoopreacher-picks',version:1,season,picks,exportedAt:new Date().toISOString()});
  function persist(){try{localStorage.setItem(key,JSON.stringify(documentData()));saved=true;tell('Picks saved in this browser. Export a copy for backup.');}catch{saved=false;tell('Browser saving is unavailable. Export your picks before leaving this page.');}}
  try{const raw=localStorage.getItem(key);if(raw){picks=validate(JSON.parse(raw));saved=true;tell('Your saved picks are loaded.');}else tell('Choose your top 10 teams in each conference. Picks save automatically.');}catch{tell('Saved picks could not be loaded. Import a backup or choose new picks.');}
  const el=(tag,text)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;return n;};
  function render(){
    const root=document.getElementById('pick-conferences');root.replaceChildren();let matches=0,compared=0,count=0;
    const tabs=el('div');tabs.className='conference-tabs';tabs.setAttribute('role','tablist');tabs.setAttribute('aria-label','Choose conference');root.append(tabs);
    const tabButtons={},panels={};
    const activate=(conf,focus=false)=>{
      activeConference=conf;
      for(const name of ['East','West']){
        const selected=name===conf;
        tabButtons[name].setAttribute('aria-selected',String(selected));
        tabButtons[name].tabIndex=selected?0:-1;
        panels[name].hidden=!selected;
      }
      if(focus)tabButtons[conf].focus();
    };
    for(const conf of ['East','West']){
      const tab=el('button',conf==='East'?'BITE':'BITW');tab.type='button';tab.id='conference-tab-'+conf;tab.setAttribute('role','tab');tab.setAttribute('aria-label',conf==='East'?'BITE — Eastern Conference':'BITW — Western Conference');tab.setAttribute('aria-controls','conference-panel-'+conf);
      tab.onclick=()=>activate(conf);
      tab.onkeydown=event=>{
        if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return;
        event.preventDefault();activate(event.key==='Home'?'East':event.key==='End'?'West':activeConference==='East'?'West':'East',true);
      };
      tabs.append(tab);tabButtons[conf]=tab;
      const section=el('section');section.className='conference';section.id='conference-panel-'+conf;section.setAttribute('role','tabpanel');section.setAttribute('aria-labelledby',tab.id);panels[conf]=section;const title=el('div');title.className='conference-title';title.append(el('h2',conf+'ern Conference'),el('span','YOUR TOP 10'));section.append(title);
      const wrap=el('div');wrap.className='table-wrap';const table=el('table'),head=el('thead'),header=el('tr'),body=el('tbody');
      ['Pick','Team','Now','W–L','Win %','Gap'].forEach((label,col)=>{const th=el('th');th.scope='col';th.setAttribute('aria-sort','none');const button=el('button',label+' ↕');button.className='static-sort';button.type='button';button.onclick=()=>{const desc=th.getAttribute('aria-sort')==='ascending';const rows=[...body.rows];rows.sort((a,b)=>{let x=a._values[col],y=b._values[col];if(x===null||y===null)return x===null?(y===null?0:1):-1;return(typeof x==='number'?x-y:x.localeCompare(y))*(desc?-1:1);});rows.forEach(r=>body.append(r));[...header.cells].forEach(h=>{h.setAttribute('aria-sort','none');h.firstChild.textContent=h._label+' ↕';});th.setAttribute('aria-sort',desc?'descending':'ascending');button.textContent=label+(desc?' ↓':' ↑');};th._label=label;th.append(button);header.append(th);});
      head.append(header);table.append(head,body);
      picks[conf].forEach((id,i)=>{
        const team=byId.get(id),rank=team&&team.WINS+team.LOSSES>0&&team.PlayoffRank>=1&&team.PlayoffRank<=15?team.PlayoffRank:null,gap=rank===null?null:rank-i-1;
        if(team)count++;if(rank!==null){compared++;if(gap===0)matches++;}
        const row=el('tr');if(gap===0)row.className='match';row._values=[i+1,team?team.TeamCity+' '+team.TeamName:null,rank,team?team.WINS*1000-team.LOSSES:null,team?.WinPCT??null,gap];row.append(el('td',i+1));
        const cell=el('td'),select=el('select');select.setAttribute('aria-label',conf+' pick '+(i+1));const empty=el('option','Choose team');empty.value='';select.append(empty);
        teams.filter(t=>t.Conference===conf).sort((a,b)=>(a.TeamCity+a.TeamName).localeCompare(b.TeamCity+b.TeamName)).forEach(t=>{const option=el('option',t.TeamCity+' '+t.TeamName);option.value=String(t.TeamID);option.selected=t.TeamID===id;option.disabled=picks[conf].includes(t.TeamID)&&t.TeamID!==id;select.append(option);});
        select.onchange=()=>{const value=select.value?Number(select.value):null;if(value!==null&&picks[conf].some((v,j)=>j!==i&&v===value))return;picks[conf][i]=value;persist();render();document.querySelector(`[aria-label="${conf} pick ${i+1}"]`).focus();};const picker=el('label');picker.className='team-picker';const selectedName=el('span',team?team.TeamCity+' '+team.TeamName:'Choose team');selectedName.className='team-picker-name';selectedName.setAttribute('aria-hidden','true');picker.append(selectedName,select);cell.append(picker);row.append(cell,el('td',rank??'—'),el('td',team?team.WINS+'–'+team.LOSSES:'—'),el('td',team?(team.WinPCT*100).toFixed(1)+'%':'—'),el('td',gap===null?'—':gap===0?'Match':gap));body.append(row);
      });wrap.append(table);section.append(wrap);root.append(section);
    }
    activate(activeConference);
    document.getElementById('pick-matches').textContent=compared?matches:'—';document.getElementById('pick-rate').textContent=compared?(matches/compared*100).toFixed(1)+'%':'—';document.getElementById('pick-compared').textContent=compared+' ranked picks compared';document.getElementById('pick-count').textContent=count+' / 20';
  }
  document.getElementById('export-picks').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(documentData(),null,2)],{type:'application/json'}));const a=el('a');a.href=url;a.download='nba-picks-'+season+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);tell('Picks exported. Keep the downloaded file as your backup.');};
  const file=document.getElementById('pick-file');document.getElementById('import-picks').onclick=()=>file.click();
  file.onchange=async()=>{try{const selected=file.files[0];if(!selected)return;if(selected.size>100000)throw Error('This file is too large to be a picks backup.');const next=validate(JSON.parse(await selected.text()));if(Object.values(picks).flat().some(v=>v!==null)&&!confirm('Replace your current picks with the imported picks?'))return;picks=next;persist();render();tell(saved?'Picks imported and saved.':'Picks imported. Browser saving is unavailable; keep your backup.');}catch(error){tell('Import failed: '+error.message+' Your current picks have not changed.');}finally{file.value='';}};
  window.addEventListener('storage',event=>{if(event.key===key)tell('Picks changed in another tab. Reload to load those changes before editing.');});
  render();
})();
