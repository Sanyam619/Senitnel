#[derive(Clone,Debug)] pub struct RootLink{pub zone:String,pub child:String,pub digest:String,pub start:i64,pub end:i64}
#[derive(Clone,Debug)] pub struct Node{pub zone:String,pub id:String,pub role:String,pub digest:String,pub start:i64,pub end:i64,pub withdrawn_after:Option<i64>}
#[derive(Clone,Debug)] pub struct Bridge{pub zone:String,pub child:String,pub issuer:String,pub start:i64,pub end:i64}
#[derive(Clone,Debug)] pub struct Record{pub zone:String,pub name:String,pub body:String}
#[derive(Clone,Debug)] pub struct Mark{pub zone:String,pub name:String,pub signer:String,pub label:String,pub start:i64,pub end:i64}
#[derive(Clone,Debug)] pub struct Query{pub id:String,pub name:String,pub instant:i64}
#[derive(Clone,Debug)] pub struct Outcome{pub id:String,pub name:String,pub instant:i64,pub status:String,pub chain:Vec<String>,pub reason:String}
#[derive(Default,Debug)] pub struct CaseData{pub roots:Vec<RootLink>,pub nodes:Vec<Node>,pub bridges:Vec<Bridge>,pub records:Vec<Record>,pub marks:Vec<Mark>,pub queries:Vec<Query>}
pub fn span(t:i64,start:i64,end:i64)->bool{t>=start&&t<end}
