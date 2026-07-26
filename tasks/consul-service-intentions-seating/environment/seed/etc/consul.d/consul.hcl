# consul agent — mesh lab
datacenter = "lab-mesh"
data_dir   = "/var/lib/consul"
node_name  = "mesh-agent"

connect {
  enabled = true
}

# Per-service node bindings live in conf.d/ drop-ins.
# Mesh allow/deny surface sheet lives in intentions.d/.
