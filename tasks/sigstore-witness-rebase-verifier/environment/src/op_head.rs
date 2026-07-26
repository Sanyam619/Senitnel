use crate::types::*;

pub enum HeadResolution {
    Bound(Checkpoint),
    Unattested,
    Missing,
}

pub fn choose_head(shards: &ShardBook, _event: &Event) -> HeadResolution {
    let mut latest: Option<Checkpoint> = None;
    for shard in shards.by_id.values() {
        for cp in &shard.checkpoints {
            let take = match &latest {
                None => true,
                Some(cur) => cp.epoch > cur.epoch,
            };
            if take {
                latest = Some(cp.clone());
            }
        }
    }
    match latest {
        Some(cp) => HeadResolution::Bound(cp),
        None => HeadResolution::Missing,
    }
}
