# The Arabic font bundle

`ArabicTranslation/arabicfont` is a Unity asset bundle (`UnityFS` container) holding one file:

```
Assets/NotoSansArabic-VariableFont_wdth,wght.ttf
```

That is Google's [Noto Sans Arabic](https://fonts.google.com/noto/specimen/Noto+Sans+Arabic) variable font, unmodified, licensed under the SIL Open Font License 1.1.

`ArabicTranslation.cs` registers it with Interplanetary Polyglot:

```csharp
api.AddLanguageFont(this, "Arabic", "arabicfont", "Assets/NotoSansArabic-VariableFont_wdth,wght.ttf");
```

## Rebuilding the bundle

Asset bundles must be built with the same Unity version as the game, **2019.4.27f1**. The steps follow the [Interplanetary Polyglot font guide](https://github.com/xen-42/outer-wilds-localization-utility/blob/main/docs/fonts.md):

1. Install Unity Hub and add editor version 2019.4.27f1.
2. Create an empty project. Before opening it, copy `NotoSansArabic-VariableFont_wdth,wght.ttf` into its `Assets/` folder.
3. Open the project, enable the Asset Bundle Browser package, and open it from `Window > AssetBundle Browser`.
4. On the Configure tab, drag the font from the Project window into a bundle named `arabicfont`.
5. Build, then copy the resulting `arabicfont` file (no extension) to `ArabicTranslation/arabicfont`.

Because this step needs the Unity editor it is not part of the CI build. The bundle is committed as a binary and its origin is documented here.
