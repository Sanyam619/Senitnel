# The runner must adopt selected_kernel for all post-checkpoint work
# regardless of what any individual checkpoint's source_kernel entry says.
# When the two disagree, selected_kernel wins by policy.
selected_kernel = wendland_c4
authority = policy_over_checkpoint
