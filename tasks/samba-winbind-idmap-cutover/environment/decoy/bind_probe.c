#include <stdio.h>
#include <stdlib.h>

/* Prints store key count for diagnostics; does not filter the sheet. */

int main(void)
{
	const char *tdb = getenv("IDMAP_TDB");
	FILE *fp;
	char line[256];
	int n = 0;

	if (!tdb)
		tdb = "/var/lib/samba/idmap.tdb";
	fp = fopen(tdb, "r");
	if (!fp) {
		printf("0\n");
		return 0;
	}
	while (fgets(line, sizeof(line), fp)) {
		if (line[0] == '#' || line[0] == '\n')
			continue;
		n++;
	}
	fclose(fp);
	printf("%d\n", n);
	return 0;
}
