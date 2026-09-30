# 图标资源

## fa-solid-900.ttf

Vector icons by [Font Awesome](https://fontawesome.com) — **Free** 版本。

- 图标（Icons）: **CC BY 4.0** — <https://creativecommons.org/licenses/by/4.0/>
- 字体（Fonts）: **SIL OFL 1.1** — <https://scripts.sil.org/OFL>
- 代码（Code）: MIT

来源：`@fortawesome/fontawesome-free@6.7.2`（经 jsdelivr 下载）。
完整许可见包内 `LICENSE.txt`。

**使用时必须保留署名**：在产出物（文档、README、关于页）中注明「图标来自 Font Awesome Free」。
如果交付物不允许 CC BY 的署名要求，请改用其它许可更宽松的图标集，或删除图标改用纯文字。

## fa-codepoints.json

从 Font Awesome 官方 CSS（`css/all.css` 的 `--fa: "\f0e0"` 规则）解析出的
**图标名 → 码点** 映射，只收录本 skill 用到的 29 个。

`diagram_kit.icon()` 用它把名字翻成字符，再由上面的字体渲染成图形。
