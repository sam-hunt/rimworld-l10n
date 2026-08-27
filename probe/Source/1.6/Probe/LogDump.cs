using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Text;
using RimWorld;
using Verse;

namespace L10nProbe;

// Dumps the game's own in-memory log — Verse.Log.Messages — to JSON so the family's startup
// smoke gate (rimworld-l10n/smoke/startup_smoke.py) can read message LEVELS authoritatively.
//
// Why this exists: on RimWorld 1.6 (Unity 2022.3, Windows player build) Player.log carries NO
// stack trace under Debug.LogError/LogWarning, so a plain Log.Error is indistinguishable
// from a Log.Message in the text file — the level is simply not recorded anywhere on disk.
// Verse.Log keeps every message it emitted as a LogMessage with its LogMessageType, so the
// probe, which already runs after every mod has loaded and logged, is the right place to
// persist that queue. (Decompile-verified, 1.6.4871: Log.Messages is a static
// IEnumerable<LogMessage>; LogMessage has public `text`, `type`, `repeats` fields and a
// `StackTrace` property that RimWorld fills itself via StackTraceUtility.ExtractStackTrace,
// independent of Unity's player stack-trace setting.)
//
// Two caps in the queue shape what a reader can trust (both decompile-verified):
//   - LogMessageQueue.maxMessages = 1000 distinct messages; the OLDEST is dropped past that.
//     meta.queueCapacity records the live value (reflection, null if unreadable) so a reader
//     can flag a dump whose count reached it as possibly truncated.
//   - a run of identical consecutive messages merges into one LogMessage with `repeats`
//     capped at 99, so `repeats` is a floor, not an exact count, at 99.
// Messages that never pass through Verse.Log — a raw unhandled exception Unity logs itself —
// are NOT in this queue; the reader still needs Player.log for those.
//
// Same failure contract as the def-injection dumps: write to a temp name and rename on
// success, and delete any stale file first, so a reader never mistakes an old dump for a
// fresh one. Any exception is logged with the [L10nProbe] prefix and swallowed by the caller
// — a dump failure must never stop the automated shutdown.
internal static class LogDump
{
    public const string FileName = "log-messages.json";

    // Schema version for the reader. Bump when a field changes meaning or is removed; adding
    // an optional field does not need a bump.
    private const int Schema = 1;

    public static string DefaultPath => Path.Combine(L10nProbeSettings.DefaultOutputDir, FileName);

    // Writes the dump and returns the path. `trigger` says which probe trigger fired, purely
    // for the file's meta block.
    public static string Write(string path, string trigger)
    {
        string dir = Path.GetDirectoryName(path);
        if (!dir.NullOrEmpty())
        {
            Directory.CreateDirectory(dir);
        }
        string tmpPath = path + ".tmp";
        File.WriteAllText(tmpPath, Build(trigger), new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
        if (File.Exists(path))
        {
            File.Delete(path);
        }
        File.Move(tmpPath, path);
        return path;
    }

    private static string Build(string trigger)
    {
        // Snapshot under Log.LockMessages(): NOT a mutex — it bumps Log.logDisablers so every
        // Verse.Log call is a no-op while held (decompile-verified), which is how the game's own
        // log window enumerates the live queue without a concurrent Enqueue invalidating the
        // enumerator. A message another thread logs during the copy is dropped, not deferred;
        // the copy is microseconds on the main thread, so that is the accepted trade.
        List<LogMessage> messages = new List<LogMessage>();
        using (Log.LockMessages())
        {
            messages.AddRange(Log.Messages);
        }

        StringBuilder sb = new StringBuilder();
        sb.Append("{\n");
        sb.Append("  \"meta\": {\n");
        sb.Append("    \"schema\": ").Append(Schema).Append(",\n");
        sb.Append("    \"gameBuild\": ");
        ProbeJson.AppendString(sb, VersionControl.CurrentVersionStringWithRev);
        sb.Append(",\n");
        sb.Append("    \"trigger\": ");
        ProbeJson.AppendString(sb, trigger);
        sb.Append(",\n");
        sb.Append("    \"messageCount\": ").Append(messages.Count).Append(",\n");
        sb.Append("    \"queueCapacity\": ").Append(QueueCapacity()?.ToString(CultureInfo.InvariantCulture) ?? "null").Append(",\n");
        sb.Append("    \"generated\": ");
        ProbeJson.AppendString(sb, DateTime.UtcNow.ToString("yyyy-MM-dd'T'HH:mm:ss'Z'", CultureInfo.InvariantCulture));
        sb.Append("\n  },\n");

        sb.Append("  \"messages\": [");
        bool first = true;
        foreach (LogMessage message in messages)
        {
            sb.Append(first ? "\n" : ",\n");
            first = false;
            sb.Append("    {\"type\": ");
            ProbeJson.AppendString(sb, message.type.ToString());
            sb.Append(", \"repeats\": ").Append(message.repeats);
            sb.Append(", \"text\": ");
            ProbeJson.AppendString(sb, message.text);
            sb.Append(", \"stackTrace\": ");
            ProbeJson.AppendString(sb, message.StackTrace);
            sb.Append('}');
        }
        sb.Append(first ? "]\n" : "\n  ]\n");
        sb.Append("}\n");
        return sb.ToString();
    }

    // Log.messageQueue and LogMessageQueue.maxMessages are private/public respectively but
    // the queue itself is not exposed; a read-only reflection peek is the only way to record
    // the cap, and a null here just means the reader cannot judge truncation.
    private static int? QueueCapacity()
    {
        try
        {
            FieldInfo queueField = typeof(Log).GetField("messageQueue", BindingFlags.Static | BindingFlags.NonPublic);
            object queue = queueField?.GetValue(null);
            FieldInfo capField = queue?.GetType().GetField("maxMessages", BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
            return capField?.GetValue(queue) as int?;
        }
        catch (Exception)
        {
            return null;
        }
    }
}
