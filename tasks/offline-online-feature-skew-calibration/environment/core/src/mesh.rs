use crate::base::FeatMap;

pub fn mesh_k(on: &FeatMap, shadow: &FeatMap, _sel: &str) -> FeatMap {
    let mut out = on.clone();
    if let Some(v) = shadow.get("f_zip") {
        out.insert("f_zip".to_string(), *v);
    }
    out
}
