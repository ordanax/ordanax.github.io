# Jekyll Bootstrap 4 Boilerplate Theme + Docker

Demo: https://ordanax.github.io/

This is a complete Dockerized Jekyll setup with a custom Bootstrap 4 theme. The setup is compatible with Github Pages: there are no unsupported plugins here.

You can ignore Docker stuff if you want and use Jekyll directly.

## Usage with Docker

Building:

```
make build
```

Serving:

```
make serve
```

Then open [http://localhost:4000](http://localhost:4000).

## Usage without Docker

```bash
# clone repo 
git clone git@github.com:ordanax/jekyll-bootstrap4-docker.git

# cd and install jekyll
cd jekyll-bootstrap4-docker
sudo gem install jekyll

# start
bundle exec jekyll serve
```

Then open [http://localhost:4000](http://localhost:4000).

## Todo

- [x] OG-tags support
- [ ] Bootstrap SASS