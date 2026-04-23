# frontend

## Project setup
```
npm install
```

### Compiles and hot-reloads for development
```
npm run serve
```

### Compiles and minifies for production
```
npm run build
```

### Lints and fixes files
```
npm run lint
```

### Customize configuration
See [Configuration Reference](https://cli.vuejs.org/config/).

## Button styles — `modern-ui` opt-out

There is a legacy global CTA layer in `src/styles/revolut-refresh.css` that
paints every `<button>` in `#app` as a blue gradient capsule unless its class
is listed in a long `:not(...)` chain. Old views rely on that look.

**New features must NOT touch that chain.** Instead, add `modern-ui` (or the
attribute `data-modern-ui`) on the root element of the view:

```vue
<template>
  <div class="my-feature modern-ui">
    <button class="mf-btn">...</button>
  </div>
</template>
```

Inside a `modern-ui` subtree the global capsule rules do not apply, so your
scoped component CSS (e.g. `.mf-btn { background: #fff; ... }`) works with
its natural specificity — no `!important`, no :hover fights. See the
`MODERN-UI OPT-OUT` comment block in `revolut-refresh.css` for details.
