# Cargo crates downloader

A simple script designed for downloading crates from Rust cargo.io.  

---

## How to use

First argument is positional argument. It specifies a path to `Cargo.lock` file and is required.

| Short key | Long key        | Description                                | Type   | Required |
|-----------|-----------------|--------------------------------------------|--------|----------|
| -h        | --help          | Show help                                  | Flag   | No       |
| -o        | --overwrite     | Overwrite existing crates                  | String | No       |
| -r        | --repo          | Crates repo link                           | String | No       |
| -O        | --output        | Output directory                           | String | No       |
| -e        | --exit-on-error | Exit program if download error encountered | Flag   | No       |

Example:

```shell
python3 crate_downloader.py Cargo.lock --output="~/CratesBareMinimumMirror"
```   

Next you'll need to fork cargo index https://github.com/rust-lang/crates.io-index and change `config.json`:

```json
{
  "dl": "http://localhost/api/v1/crates",
  "api": "http://localhost/"
}
```

Push to your git and change `.cargo/.config.toml`:

```toml
[source]

[source.mirror]
registry = "https://github.com/YOUR_NAME/crates.io-index.git"

[source.crates-io]
replace-with = "mirror"
```

It's possible to use other git repositories.
