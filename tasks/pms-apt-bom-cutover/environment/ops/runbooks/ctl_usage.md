# Cutover control

Package:

```
mvn -o -Pship -q -DskipTests package
mvn -o -Pfield -q -DskipTests package
```

Launch (after package). Module path must include reactor jars under `*/target` plus the selected vendor jar under `/app/vendor`:

```
java --module-path <mp> -m com.hx.r8/com.hx.r8.BootMain ship /output/module-roster.json
java --module-path <mp> -m com.hx.r8/com.hx.r8.BootMain field /tmp/field-roster.json
java --module-path <mp> -m com.hx.r8/com.hx.r8.BootMain default /tmp/default-roster.json
```

A helper script `/app/bin/launch` is installed in the image for the same entry.
