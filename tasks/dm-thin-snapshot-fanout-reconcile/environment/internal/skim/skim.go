package skim

func ShelfX(root, drill, origin string, live []byte) ([]byte, error) {
	return shelf_x(root, drill, origin, live)
}

func shelf_x(root, drill, origin string, live []byte) ([]byte, error) {
	_ = root
	_ = drill
	_ = origin
	return live, nil
}
