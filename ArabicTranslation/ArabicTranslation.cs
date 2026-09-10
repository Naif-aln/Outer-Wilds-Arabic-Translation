using OWML.Common;
using OWML.ModHelper;
using System;
using System.Collections.Generic;
using System.Text;

namespace ArabicTranslation
{
    public class ArabicTranslation : ModBehaviour
    {
        private void Start()
        {
            var api = ModHelper.Interaction.TryGetModApi<ILocalizationAPI>("xen.LocalizationUtility");
            if (api == null)
            {
                ModHelper.Console.WriteLine("Could not find Interplanetary Polyglot!", MessageType.Error);
                return;
            }

            api.RegisterLanguage(this, "Arabic", "Translation_Arabic.xml");
            api.AddLanguageFont(this, "Arabic", "arabicfont", "Assets/NotoSansArabic-VariableFont_wdth,wght.ttf");
            api.AddLanguageFixer("Arabic", ArabicSupport.Fix);

            ModHelper.Console.WriteLine("Arabic Translation loaded!", MessageType.Success);
        }
    }

    public interface ILocalizationAPI
    {
        void RegisterLanguage(ModBehaviour mod, string name, string translationPath);
        void AddLanguageFont(ModBehaviour mod, string name, string assetBundlePath, string fontPath);
        void AddLanguageFixer(string name, Func<string, string> fixer);
    }

    public static class ArabicSupport
    {
        // The dialogue box fits about 55 shaped Arabic chars per line
        private const int WRAP_WIDTH = 55;

        public static string Fix(string str)
        {
            if (string.IsNullOrEmpty(str)) return str;

            // First shape all Arabic letters on each existing line
            var lines = str.Split('\n');
            var shaped = new string[lines.Length];
            for (int i = 0; i < lines.Length; i++)
                shaped[i] = FixLine(lines[i]);

            // Join back to one string
            string result = string.Join("\n", shaped);

            // If it's a single long line (typical dialogue entry),
            // pre-wrap it so Unity doesn't need to — and reverse the
            // line order so Unity's bidi reversal cancels out.
            // Ship log entries come through as multiple short lines
            // already wrapped by the game, so we skip them.
            if (lines.Length == 1 && result.Length > WRAP_WIDTH)
            {
                return PreWrap(result);
            }

            return result;
        }

        static string PreWrap(string str)
        {
            // Split into words and wrap at WRAP_WIDTH
            var words = str.Split(' ');
            var wrappedLines = new List<string>();
            var current = new StringBuilder();

            foreach (var word in words)
            {
                if (current.Length > 0 && current.Length + 1 + word.Length > WRAP_WIDTH)
                {
                    wrappedLines.Add(current.ToString());
                    current.Clear();
                }
                if (current.Length > 0) current.Append(' ');
                current.Append(word);
            }
            if (current.Length > 0)
                wrappedLines.Add(current.ToString());

            // If only one line after wrapping, no reversal needed
            if (wrappedLines.Count == 1)
                return wrappedLines[0];

            // Reverse so Unity's line-order reversal cancels out
            wrappedLines.Reverse();
            return string.Join("\n", wrappedLines);
        }

        static string FixLine(string str)
        {
            if (string.IsNullOrEmpty(str)) return str;

            var tokens = Tokenize(str);
            var result = new List<string>();

            foreach (var token in tokens)
            {
                if (ContainsArabic(token))
                    result.Insert(0, ReshapeWord(token));
                else
                    result.Add(token);
            }

            return string.Join(" ", result);
        }

        static List<string> Tokenize(string str)
        {
            var tokens = new List<string>();
            var current = new StringBuilder();

            foreach (char c in str)
            {
                if (c == ' ')
                {
                    if (current.Length > 0)
                    {
                        tokens.Add(current.ToString());
                        current.Clear();
                    }
                }
                else
                {
                    current.Append(c);
                }
            }
            if (current.Length > 0)
                tokens.Add(current.ToString());

            return tokens;
        }

        static bool ContainsArabic(string s)
        {
            foreach (char c in s)
                if (c >= 0x0600 && c <= 0x06FF) return true;
            return false;
        }

        static string ReshapeWord(string word)
        {
            word = ApplyLamAlef(word);
            var sb = new StringBuilder();
            char[] chars = word.ToCharArray();

            for (int i = 0; i < chars.Length; i++)
            {
                char c = chars[i];
                if (c == '\0') continue;

                bool prevConnects = i > 0 && chars[i-1] != '\0' && IsArabic(chars[i-1]) && CanConnectLeft(chars[i-1]);
                bool nextConnects = i < chars.Length - 1 && chars[i+1] != '\0' && IsArabic(chars[i+1]);

                char shaped = Shape(c, prevConnects, nextConnects);
                sb.Insert(0, shaped);
            }
            return sb.ToString();
        }

        static string ApplyLamAlef(string word)
        {
            word = word.Replace("\u0644\u0622", "\uFEF5\0");
            word = word.Replace("\u0644\u0623", "\uFEF7\0");
            word = word.Replace("\u0644\u0625", "\uFEF9\0");
            word = word.Replace("\u0644\u0627", "\uFEFB\0");
            return word;
        }

        static bool IsArabic(char c) =>
            (c >= 0x0621 && c <= 0x064A) ||
            (c >= 0xFE70 && c <= 0xFEFF) ||
            (c >= 0x0671 && c <= 0x06D3);

        static bool CanConnectLeft(char c)
        {
            string rightOnly = "\u0621\u0622\u0623\u0624\u0625\u0627\u0629\u062F\u0630\u0631\u0632\u0648\u0649\u0671\u0672\u0673\u0675";
            return !rightOnly.Contains(c.ToString());
        }

        static char Shape(char c, bool prev, bool next)
        {
            int form = prev ? (next ? 3 : 1) : (next ? 2 : 0);
            var table = GetTable(c);
            if (table == null || table[form] == 0) return c;
            return (char)table[form];
        }

        static int[] GetTable(char c)
        {
            switch (c)
            {
                case '\u0621': return new[] { 0xFE80, 0xFE80, 0, 0 };
                case '\u0622': return new[] { 0xFE81, 0xFE82, 0, 0 };
                case '\u0623': return new[] { 0xFE83, 0xFE84, 0, 0 };
                case '\u0624': return new[] { 0xFE85, 0xFE86, 0, 0 };
                case '\u0625': return new[] { 0xFE87, 0xFE88, 0, 0 };
                case '\u0626': return new[] { 0xFE89, 0xFE8A, 0xFE8B, 0xFE8C };
                case '\u0627': return new[] { 0xFE8D, 0xFE8E, 0, 0 };
                case '\u0628': return new[] { 0xFE8F, 0xFE90, 0xFE91, 0xFE92 };
                case '\u0629': return new[] { 0xFE93, 0xFE94, 0, 0 };
                case '\u062A': return new[] { 0xFE95, 0xFE96, 0xFE97, 0xFE98 };
                case '\u062B': return new[] { 0xFE99, 0xFE9A, 0xFE9B, 0xFE9C };
                case '\u062C': return new[] { 0xFE9D, 0xFE9E, 0xFE9F, 0xFEA0 };
                case '\u062D': return new[] { 0xFEA1, 0xFEA2, 0xFEA3, 0xFEA4 };
                case '\u062E': return new[] { 0xFEA5, 0xFEA6, 0xFEA7, 0xFEA8 };
                case '\u062F': return new[] { 0xFEA9, 0xFEAA, 0, 0 };
                case '\u0630': return new[] { 0xFEAB, 0xFEAC, 0, 0 };
                case '\u0631': return new[] { 0xFEAD, 0xFEAE, 0, 0 };
                case '\u0632': return new[] { 0xFEAF, 0xFEB0, 0, 0 };
                case '\u0633': return new[] { 0xFEB1, 0xFEB2, 0xFEB3, 0xFEB4 };
                case '\u0634': return new[] { 0xFEB5, 0xFEB6, 0xFEB7, 0xFEB8 };
                case '\u0635': return new[] { 0xFEB9, 0xFEBA, 0xFEBB, 0xFEBC };
                case '\u0636': return new[] { 0xFEBD, 0xFEBE, 0xFEBF, 0xFEC0 };
                case '\u0637': return new[] { 0xFEC1, 0xFEC2, 0xFEC3, 0xFEC4 };
                case '\u0638': return new[] { 0xFEC5, 0xFEC6, 0xFEC7, 0xFEC8 };
                case '\u0639': return new[] { 0xFEC9, 0xFECA, 0xFECB, 0xFECC };
                case '\u063A': return new[] { 0xFECD, 0xFECE, 0xFECF, 0xFED0 };
                case '\u0641': return new[] { 0xFED1, 0xFED2, 0xFED3, 0xFED4 };
                case '\u0642': return new[] { 0xFED5, 0xFED6, 0xFED7, 0xFED8 };
                case '\u0643': return new[] { 0xFED9, 0xFEDA, 0xFEDB, 0xFEDC };
                case '\u0644': return new[] { 0xFEDD, 0xFEDE, 0xFEDF, 0xFEE0 };
                case '\u0645': return new[] { 0xFEE1, 0xFEE2, 0xFEE3, 0xFEE4 };
                case '\u0646': return new[] { 0xFEE5, 0xFEE6, 0xFEE7, 0xFEE8 };
                case '\u0647': return new[] { 0xFEE9, 0xFEEA, 0xFEEB, 0xFEEC };
                case '\u0648': return new[] { 0xFEED, 0xFEEE, 0, 0 };
                case '\u0649': return new[] { 0xFEEF, 0xFEF0, 0, 0 };
                case '\u064A': return new[] { 0xFEF1, 0xFEF2, 0xFEF3, 0xFEF4 };
                case '\uFEFB': return new[] { 0xFEFB, 0xFEFC, 0, 0 };
                case '\uFEF5': return new[] { 0xFEF5, 0xFEF6, 0, 0 };
                case '\uFEF7': return new[] { 0xFEF7, 0xFEF8, 0, 0 };
                case '\uFEF9': return new[] { 0xFEF9, 0xFEFA, 0, 0 };
                default: return null;
            }
        }
    }
}
