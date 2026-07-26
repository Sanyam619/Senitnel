use crate::model::{Bridge,CaseData,Mark,Node,Query,Record,RootLink};
fn f<'a>(p:&'a[&str],i:usize)->Result<&'a str,String>{p.get(i).copied().ok_or_else(||format!("missing {i}"))}
fn n(p:&[&str],i:usize)->Result<i64,String>{f(p,i)?.parse::<i64>().map_err(|e|e.to_string())}
pub fn feed_line(d:&mut CaseData,line:&str)->Result<(),String>{let line=line.trim(); if line.is_empty()||line.starts_with('#'){return Ok(())} let p:Vec<&str>=line.split('|').map(str::trim).collect(); match f(&p,0)?{
"ROOT"=>d.roots.push(RootLink{zone:f(&p,1)?.into(),child:f(&p,2)?.into(),digest:f(&p,3)?.into(),start:n(&p,4)?,end:n(&p,5)?}),
"KEY"=>d.nodes.push(Node{zone:f(&p,1)?.into(),id:f(&p,2)?.into(),role:f(&p,3)?.into(),digest:f(&p,4)?.into(),start:n(&p,5)?,end:n(&p,6)?,withdrawn_after:if f(&p,7)?=="-"{None}else{Some(n(&p,7)?)} }),
"BRIDGE"=>d.bridges.push(Bridge{zone:f(&p,1)?.into(),child:f(&p,2)?.into(),issuer:f(&p,3)?.into(),start:n(&p,4)?,end:n(&p,5)?}),
"REC"=>d.records.push(Record{zone:f(&p,1)?.into(),name:f(&p,2)?.into(),body:f(&p,3)?.into()}),
"SIG"=>d.marks.push(Mark{zone:f(&p,1)?.into(),name:f(&p,2)?.into(),signer:f(&p,3)?.into(),label:f(&p,4)?.into(),start:n(&p,5)?,end:n(&p,6)?}),
"Q"=>d.queries.push(Query{id:f(&p,1)?.into(),name:f(&p,2)?.into(),instant:n(&p,3)?}),
x=>return Err(format!("unknown {x}"))}; Ok(())}
