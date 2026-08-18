<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="zh_CN">
<context>
    <name>Btrfs</name>
    <message>
        <location filename="../src/util/Btrfs.cpp" line="115"/>
        <source>Failed to create the snapshot</source>
        <translation>Snapshots erstellen fehlgeschlagen</translation>
    </message>
    <message>
        <location filename="../src/util/Btrfs.cpp" line="380"/>
        <source>You cannot restore to the root of the partition</source>
        <translation>Du kannst die Partition nicht im Stammverzeichnis wiederherstellen.</translation>
    </message>
    <message>
        <location filename="../src/util/Btrfs.cpp" line="407"/>
        <source>Failed to make a backup of target subvolume</source>
        <translation>Sicherung des Ziel-Teilvolumens erstellen fehlgeschlagen</translation>
    </message>
    <message>
        <location filename="../src/util/Btrfs.cpp" line="428"/>
        <source>Failed to restore subvolume!</source>
        <translation>Teilvolumen wiederherstellen fehlgeschlagen!</translation>
    </message>
    <message>
        <location filename="../src/util/Btrfs.cpp" line="429"/>
        <source>Snapshot restore failed.  Please verify the status of your system before rebooting</source>
        <translation>Wiederherstellung System-Snapshots ist fehlgeschlagen. Bitte überprüfe den Status deines Systems vor dem Neustart.</translation>
    </message>
    <message>
        <location filename="../src/util/Btrfs.cpp" line="444"/>
        <source>The restore was successful but the migration of the nested subvolumes failed</source>
        <translation>Wiederherstellung war erfolgreich, aber die Migration der verschachtelten Teilvolumens schlug fehl.</translation>
    </message>
    <message>
        <location filename="../src/util/Btrfs.cpp" line="445"/>
        <source>Please migrate the those subvolumes manually</source>
        <translation>Bitte migriere diese Teilvolumen manuell</translation>
    </message>
    <message>
        <location filename="../src/util/Btrfs.cpp" line="572"/>
        <source>UUID </source>
        <translation>UUID </translation>
    </message>
</context>
<context>
    <name>BtrfsStatus</name>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="16"/>
        <location filename="../src/util/BtrfsStatus.cpp" line="55"/>
        <source>no stats available</source>
        <translation>Keine Statistiken verfügbar</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="19"/>
        <source>no errors found</source>
        <translation>Keine Fehler gefunden</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="22"/>
        <source>running</source>
        <translation>Läuft...</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="25"/>
        <source>finished</source>
        <translation>Fertiggestellt</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="28"/>
        <source>canceled</source>
        <translation>Abgebrochen</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="31"/>
        <source>aborted</source>
        <translation>Abgebrochen</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="34"/>
        <source>interrupted</source>
        <translation>Unterbrochen</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="64"/>
        <source>UUID:</source>
        <translation>UUID: </translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="65"/>
        <source>Scrub started:</source>
        <translation>Scrub (Reinigung) gestartet: </translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="66"/>
        <source>Scrub resumed:</source>
        <translation>Scrub (Reinigung) wieder aufgenommen: </translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="67"/>
        <source>Status:</source>
        <translation>Status: </translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="68"/>
        <source>Duration:</source>
        <translation>Dauer: </translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="69"/>
        <source>Time left:</source>
        <translation>Zeit übrig:</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="70"/>
        <source>ETA:</source>
        <translation>Voraussichtliche Fertigstellungszeit:</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="71"/>
        <source>Total to scrub:</source>
        <translation>Insgesamt zu reinigen:</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="72"/>
        <source>Bytes scrubbed:</source>
        <translation>Bytes bereinigt;</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="73"/>
        <source>Rate:</source>
        <translation>Bewertung: </translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="74"/>
        <source>Error summary:</source>
        <translation>Fehlerzusammenfassung:</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="75"/>
        <source>read_errors:</source>
        <translation>read_errors:</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="76"/>
        <source>csum_errors:</source>
        <translation>校验和错误：</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="77"/>
        <source>verify_errors:</source>
        <translation>verify_errors:</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="78"/>
        <source>super_errors:</source>
        <translation>super_errors: </translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="79"/>
        <source>malloc_errors:</source>
        <translation>malloc_errors: </translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="80"/>
        <source>uncorrectable_errors:</source>
        <translation>uncorrectable_errors: </translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="81"/>
        <source>unverified_errors:</source>
        <translation>unverified_errors: </translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="111"/>
        <source>No balance operation found on %1</source>
        <translation>Kein Ausgleich auf %1 gefunden</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="116"/>
        <source>Balance operation on %1 is running</source>
        <translation>Ausgleichvorgang von %1 läuft</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="121"/>
        <source>Balance operation on %1 is paused</source>
        <translation>Ausgleichsvorgang von %1 wurde angehalten</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="126"/>
        <source>Done, relocated %1 of %2 chunks</source>
        <translation>Fertig, %1 von %2 Blöcken verschoben</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="131"/>
        <source>%1 of about %2 chunks balanced (%3 considered), %4% left</source>
        <translation>%1 von etwa %2 Blöcken ausgeglichen (%3 berücksichtigt), %4 % verbleiben</translation>
    </message>
</context>
<context>
    <name>Cli</name>
    <message>
        <location filename="../src/ui/Cli.cpp" line="34"/>
        <location filename="../src/ui/Cli.cpp" line="52"/>
        <source>You must run this application as root</source>
        <translation>Anwendung muss als Root ausführt werden</translation>
    </message>
    <message>
        <location filename="../src/ui/Cli.cpp" line="61"/>
        <source>Failed to parse snapshot list</source>
        <translation>Snapshot-Liste analysieren fehlgeschlagen</translation>
    </message>
    <message>
        <location filename="../src/ui/Cli.cpp" line="69"/>
        <source>This is not a snapshot that can be restored by this application</source>
        <translation>Dies ist kein Snapshot, der mit dieser Anwendung wiederhergestellt werden kann.</translation>
    </message>
    <message>
        <location filename="../src/ui/Cli.cpp" line="78"/>
        <source>Source snapshot not found</source>
        <translation>Quell-Snapshot nicht gefunden</translation>
    </message>
    <message>
        <location filename="../src/ui/Cli.cpp" line="83"/>
        <source>Snapshot subvolume not found</source>
        <translation>Snapshot-Teilvolumen nicht gefunden</translation>
    </message>
    <message>
        <location filename="../src/ui/Cli.cpp" line="92"/>
        <source>Target not found</source>
        <translation>Ziel nicht gefunden</translation>
    </message>
    <message>
        <location filename="../src/ui/Cli.cpp" line="96"/>
        <source>Restoring snapshot %1</source>
        <translation>Snapshot %1 wiederherstellen</translation>
    </message>
    <message>
        <location filename="../src/ui/Cli.cpp" line="103"/>
        <source>Snapshot restoration complete.</source>
        <translation>Wiederherstellung des Snapshots abgeschlossen</translation>
    </message>
    <message>
        <location filename="../src/ui/Cli.cpp" line="104"/>
        <source>A copy of the original subvolume has been saved as </source>
        <translation>Kopie des ursprünglichen Teilvolumens wurde gespeichert unter </translation>
    </message>
    <message>
        <location filename="../src/ui/Cli.cpp" line="105"/>
        <source>Please reboot immediately</source>
        <translation>Bitte System jetzt neu starten</translation>
    </message>
</context>
<context>
    <name>DiffViewer</name>
    <message>
        <location filename="../src/ui/DiffViewer.ui" line="14"/>
        <source>Dialog</source>
        <translation>Dialog</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.ui" line="83"/>
        <source>Select a snapshot from the left to see the diff</source>
        <translation>Links einen Screenshot auswählen, um die Unterschiede zu sehen</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.ui" line="116"/>
        <source>Restore</source>
        <translation>Wiederherstellen</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.ui" line="123"/>
        <source>Close</source>
        <translation>Schließen</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="14"/>
        <source>Diff Viewer</source>
        <translation>Unterschied-Ansicht</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="29"/>
        <source>Confirm</source>
        <translation>Bestätigen</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="29"/>
        <source>Are you sure you want to restore this the file over the current file?</source>
        <translation>Sicher, dass du diese Datei über die aktuelle Datei wiederherstellen möchtest?</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="38"/>
        <source>Restore Failed</source>
        <translation>Wiederherstellen fehlgeschlagen</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="38"/>
        <source>The file failed to restore</source>
        <translation>Wiederherstellung der Datei fehlgeschlagen</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="42"/>
        <source>Restore File</source>
        <translation>Datei wiederherstellen</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="42"/>
        <source>The file was successfully restored</source>
        <translation>Datei wurde erfolgreich wiederhergestellt</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="63"/>
        <source>Num</source>
        <comment>The number associated with a snapshot</comment>
        <translation>Die einem Snapshot zugeordnete Nummer</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="64"/>
        <source>Date/Time</source>
        <translation>Datum/Zeit</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="65"/>
        <source>Root Path</source>
        <translation>Root-Verzeichnis</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="66"/>
        <source>File Path</source>
        <translation>Datei-Verzeichnis</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="121"/>
        <source>There are no differences between the selected files</source>
        <translation>Keine Unterschiede zwischen den ausgewählten Dateien</translation>
    </message>
</context>
<context>
    <name>FileBrowser</name>
    <message>
        <location filename="../src/ui/FileBrowser.ui" line="14"/>
        <source>Dialog</source>
        <translation>Dialog</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.ui" line="70"/>
        <source>Show Diff</source>
        <translation>Unterschied anzeigen</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.ui" line="83"/>
        <location filename="../src/ui/FileBrowser.cpp" line="93"/>
        <location filename="../src/ui/FileBrowser.cpp" line="113"/>
        <source>Restore File</source>
        <translation>Datei wiederherstellen</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.ui" line="96"/>
        <source>Close</source>
        <translation>Schließen</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.cpp" line="41"/>
        <source>Snapshot File Viewer</source>
        <translation>Snapshot-Datei-Betrachter</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.cpp" line="53"/>
        <source>File Viewer</source>
        <translation>Datei-Betrachter</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.cpp" line="70"/>
        <source>Diff File</source>
        <translation>Datei-Unterschied</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.cpp" line="71"/>
        <source> is a directory, only files can be diffed</source>
        <translation>ist ein Verzeichnis, es können nur Dateien verglichen werden</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.cpp" line="94"/>
        <source> is a directory, only files can be restored</source>
        <translation>ist ein Verzeichnis, es können nur Dateien wiederhergestellt werden</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.cpp" line="98"/>
        <source>Confirm</source>
        <translation>Bestätigen</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.cpp" line="98"/>
        <source>Are you sure you want to restore this the file over the current file?</source>
        <translation>Sicher, dass du diese Datei über die aktuelle Datei wiederherstellen möchtest?</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.cpp" line="109"/>
        <source>Restore Failed</source>
        <translation>Wiederherstellen fehlgeschlagen</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.cpp" line="109"/>
        <source>The file failed to restore</source>
        <translation>Wiederherstellung der Datei fehlgeschlagen</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.cpp" line="113"/>
        <source>The file was successfully restored</source>
        <translation>Datei wurde erfolgreich wiederhergestellt</translation>
    </message>
</context>
<context>
    <name>MainWindow</name>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="14"/>
        <source>BTRFS-Assistant</source>
        <translation>BTRFS-Assistant</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="31"/>
        <source>Overview</source>
        <translation>Überblick</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="67"/>
        <location filename="../src/ui/MainWindow.ui" line="1577"/>
        <source>Scrub</source>
        <translation>Scrub (Bereinigen)</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="108"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Perform scrub on device.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Bereinigungsvorgang auf dem Gerät durchführen&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="111"/>
        <location filename="../src/ui/MainWindow.ui" line="195"/>
        <location filename="../src/ui/MainWindow.cpp" line="159"/>
        <location filename="../src/ui/MainWindow.cpp" line="179"/>
        <source>Start</source>
        <translation>Start</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="126"/>
        <source>No scrub ran.</source>
        <translation>Kein Bereinigungslauf ausgeführt</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="151"/>
        <location filename="../src/ui/MainWindow.ui" line="1503"/>
        <source>Balance</source>
        <translation>Ausgleich</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="192"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Perform full balance on device.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Vollständigen Ausgleich am Gerät durchführen&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="214"/>
        <source>No balance ran.</source>
        <translation>Kein Ausgleich ausgeführt</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="236"/>
        <source>Internal Filesystem Statistics</source>
        <translation>Interne Dateisystemstatistiken</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="242"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Utilization percentage of system chunks in the allocated space.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Auslastung der System-Chunks im zugewiesenen Speicherbereich.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="252"/>
        <source>Data:</source>
        <translation>Daten: </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="259"/>
        <source>Metadata:</source>
        <translation>Metadaten: </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="266"/>
        <source>System:</source>
        <translation>System: </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="273"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Utilization percentage of metadata chunks in the allocated space.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Auslastungsgrad der Metadaten-Chunks im zugewiesenen Speicherbereich.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="283"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Utilization percentage of file data chunks in the allocated space.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Auslastungsgrad der Dateidaten-Chunks im zugewiesenen Speicherplatz.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="302"/>
        <source>Information</source>
        <translation>Info</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="308"/>
        <source>Used:</source>
        <translation>Verwendet: </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="315"/>
        <location filename="../src/ui/MainWindow.ui" line="392"/>
        <source>Estimate of the amount of data that can still be written to this FS, based on the current usage profile.</source>
        <translation>Schätzung der Datenmenge, die auf der Grundlage des aktuellen Nutzungsprofils noch auf dieses Dateisystem geschrieben werden kann.</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="325"/>
        <location filename="../src/ui/MainWindow.ui" line="402"/>
        <source>Minimum amount of data that you can expect to be able to get onto the filesystem. </source>
        <translation>Mindestdatenmenge, die du voraussichtlich auf dem Dateisystem unterbringen kannst.</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="345"/>
        <source>Allocated:  </source>
        <translation>Zugewiesen: </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="359"/>
        <source>Filesystem Size: </source>
        <translation>Dateisystemgröße: </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="395"/>
        <source>Free (Estimated): </source>
        <translation>Frei (geschätzt): </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="405"/>
        <source>Free (Minimum): </source>
        <translation>Frei (Minimum): </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="421"/>
        <source>Volume Selection</source>
        <translation>Volumenauswahl</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="427"/>
        <source>Filesystem:</source>
        <translation>Dateisystem: </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="463"/>
        <source>Enable Quotas</source>
        <translation>Kontingente aktivieren</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="470"/>
        <source>Refresh Btrfs Data</source>
        <translation>Btrfs-Daten aktualisieren</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="485"/>
        <source>Subvolumes</source>
        <translation>Teilvolumen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="523"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Include children subvolumes of .snapshots and timeshift folders.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Untergeordnete Teilvolumen von .snapshots- und Timeshift-Ordnern einbeziehen.。&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="526"/>
        <source>Include Timeshift and Snapper Snapshots</source>
        <translation>Timeshift- und Snapper-Snapshots einbeziehen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="536"/>
        <source>Include Container Subvolumes</source>
        <translation>Container-Teilvolumen einbeziehen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="557"/>
        <source>Filter...</source>
        <translation>Filter...</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="583"/>
        <source>Restore Backup</source>
        <translation>Sicherung wiederherstellen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="603"/>
        <location filename="../src/ui/MainWindow.ui" line="905"/>
        <source>Browse</source>
        <translation>Durchsuchen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="623"/>
        <location filename="../src/ui/MainWindow.ui" line="786"/>
        <location filename="../src/ui/MainWindow.ui" line="1070"/>
        <source>Delete</source>
        <translation>Löschen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="643"/>
        <location filename="../src/ui/MainWindow.ui" line="812"/>
        <location filename="../src/ui/MainWindow.ui" line="951"/>
        <source>Refresh</source>
        <translation>Aktualisieren</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="690"/>
        <location filename="../src/ui/MainWindow.cpp" line="871"/>
        <source>Snapper</source>
        <translation>Snapper</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="712"/>
        <source>New/Delete</source>
        <translation>Neu/Löschen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="733"/>
        <location filename="../src/ui/MainWindow.ui" line="1040"/>
        <source>Select config: </source>
        <translation>Konfiguration auswählen: </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="766"/>
        <location filename="../src/ui/MainWindow.ui" line="1063"/>
        <source>New</source>
        <translation>Neu</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="849"/>
        <source>Browse/Restore</source>
        <translation>Durchsuchen/Wiederherstellen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="870"/>
        <source>Select target: </source>
        <translation>Ziel auswählen: </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="925"/>
        <source>Restore</source>
        <translation>Wiederherstellen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="992"/>
        <source>Snapper Settings</source>
        <translation>Snapper-Einstellungen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1090"/>
        <source>Save</source>
        <translation>保存</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1100"/>
        <location filename="../src/ui/MainWindow.ui" line="1163"/>
        <source>Config Information</source>
        <translation>Konfigurationsinfos</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1106"/>
        <location filename="../src/ui/MainWindow.ui" line="1169"/>
        <source>Config name: </source>
        <translation>Konfigurationsname: </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1133"/>
        <location filename="../src/ui/MainWindow.ui" line="1196"/>
        <source>Backup path: </source>
        <translation>Sicherungsverzeichnis: </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1232"/>
        <source>Snapshot Retention</source>
        <translation>Snapshot-Beibehaltung</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1238"/>
        <location filename="../src/ui/MainWindow.ui" line="1261"/>
        <location filename="../src/ui/MainWindow.ui" line="1275"/>
        <location filename="../src/ui/MainWindow.ui" line="1282"/>
        <location filename="../src/ui/MainWindow.ui" line="1353"/>
        <source>Save: </source>
        <translation>Speichern: </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1251"/>
        <location filename="../src/ui/MainWindow.ui" line="1289"/>
        <source>Timeline snapshots are taken hourly, the cleanup job reduces the snapshots in accordance with the below settings</source>
        <translation>Timeline-Snapshots werden stündlich erstellt, der Bereinigungsjob reduziert die Snapshots gemäß den untenstehenden Einstellungen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1254"/>
        <source>Enable timeline snapshots</source>
        <translation>Zeitachsen-Snapshots aktivieren</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1268"/>
        <source>Daily</source>
        <translation>Täglich</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1308"/>
        <source>Yearly</source>
        <translation>Jährlich</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1315"/>
        <source>Monthly</source>
        <translation>Monatlich</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1325"/>
        <source>Hourly</source>
        <translation>Stündlich</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1332"/>
        <source>Weekly</source>
        <translation>Wöchentlich</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1339"/>
        <source>Save:</source>
        <translation>Speichern:</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1346"/>
        <source>Number</source>
        <translation>Nummer</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1382"/>
        <source>systemd Unit Settings</source>
        <translation>systemd-Einheit-Einstellungen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1388"/>
        <source>Snapper timeline enabled</source>
        <translation>Snapper-Zeitachse aktiviert</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1401"/>
        <source>Snapper cleanup enabled</source>
        <translation>Snapper-Bereinigung aktiviert</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1414"/>
        <source>Snapper boot enabled</source>
        <translation>Snapper-Bootvorgang aktiviert</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1433"/>
        <source>Apply systemd changes</source>
        <translation>systemd-Änderungen anwenden</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1461"/>
        <source>Btrfs maintenance</source>
        <translation>Btrfs-Wartung</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1531"/>
        <location filename="../src/ui/MainWindow.ui" line="1621"/>
        <location filename="../src/ui/MainWindow.ui" line="1695"/>
        <source>Frequency: </source>
        <translation>Häuffigkeit: </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1541"/>
        <location filename="../src/ui/MainWindow.ui" line="1628"/>
        <location filename="../src/ui/MainWindow.ui" line="1702"/>
        <source>Select All</source>
        <translation>Alle</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1548"/>
        <location filename="../src/ui/MainWindow.ui" line="1635"/>
        <location filename="../src/ui/MainWindow.ui" line="1709"/>
        <source>Mountpoints: </source>
        <translation>Einhängepunkte: </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1651"/>
        <source>Defrag</source>
        <translation>Defragmentieren</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1747"/>
        <source>Reset</source>
        <translation>Zurücksetzen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1767"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Update Btrfs Maintenance config file and call service to load new settings.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Btrfs-Wartungskonfigurationsdatei aktualisieren und den Dienst aufrufen, um die neuen Einstellungen zu laden.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1770"/>
        <source>Apply</source>
        <translation>Anwenden</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="59"/>
        <source>The application must be run as the superuser(root)</source>
        <translation>Anwendung muss als Superuser (root) ausgeführt werden</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="87"/>
        <source>Error</source>
        <translation>Fehler</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="318"/>
        <source>You have lots of free space, did you overbuy?</source>
        <translation>Du hast jede Menge freien Speicherplatz – hast du zu viel gekauft?</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="320"/>
        <source>Situation critical!  Time to delete some data or buy more disk</source>
        <translation>Die Lage ist kritisch! Es ist an der Zeit, einige Daten zu löschen oder mehr Speicherplatz zu kaufen.</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="322"/>
        <source>Your disk space is well utilized</source>
        <translation>Dein Speicherplatz wird gut genutzt</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="374"/>
        <location filename="../src/ui/MainWindow.cpp" line="424"/>
        <source>Number</source>
        <comment>Nummer, die einem Snapshot zugeordnet ist</comment>
        <translation>Nummer</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="375"/>
        <location filename="../src/ui/MainWindow.cpp" line="428"/>
        <source>Date/Time</source>
        <translation>Datum/Zeit</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="376"/>
        <location filename="../src/ui/MainWindow.cpp" line="429"/>
        <source>Type</source>
        <translation>Typ</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="377"/>
        <source>Cleanup</source>
        <translation>Bereinigen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="378"/>
        <location filename="../src/ui/MainWindow.cpp" line="431"/>
        <source>Description</source>
        <translation>Beschreibung</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="426"/>
        <source>Subvolume</source>
        <translation>Teilvolumen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="542"/>
        <source>This is not a snapshot that can be restored by this application</source>
        <translation>Dies ist kein Snapshot, der mit dieser Anwendung wiederhergestellt werden kann</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="552"/>
        <source>Snapshot subvolume not found</source>
        <translation>Snapshot-Subvolume nicht gefunden</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="562"/>
        <source>Target not found</source>
        <translation>Ziel nicht gefunden</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="568"/>
        <source>Warning subvolid mount detected!</source>
        <translation>Warnung: Subvolid-Einbindung erkannt!</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="569"/>
        <source>It appears you are currently mounting by subvolid.  Doing a restore in this case may not produce the expected outcome.  It is highly recommended you switch to mounting by subvolume path before proceeding!</source>
        <translation>Es scheint, als würdest du das Teilvolumen derzeit über die Subvol-ID einbinden. Eine Wiederherstellung könnte in diesem Fall nicht das erwartete Ergebnis liefern. Es wird dringend empfohlen, vor dem Fortfahren auf das Einbinden über den Teilvolumen-Pfad zu wechseln!</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="574"/>
        <source>Are you sure you want to restore </source>
        <translation>Sicher, dass du wiederherstellen möchtest?</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="574"/>
        <source> to </source>
        <comment>wie bei von/bis</comment>
        <translation> zu </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="588"/>
        <source>Snapshot Restore</source>
        <translation>Snapshot wiederherstellen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="589"/>
        <source>Snapshot restoration complete.</source>
        <translation>Wiederherstellung des Snapshots abgeschlossen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="589"/>
        <location filename="../src/ui/MainWindow.cpp" line="1544"/>
        <source>A copy of the original subvolume has been saved as </source>
        <translation>Eine Kopie des ursprünglichen Teilvolumens wurde gespeichert als </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="590"/>
        <location filename="../src/ui/MainWindow.cpp" line="1545"/>
        <source>Please reboot immediately</source>
        <translation>Bitte den Computer sofort neu starten.</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="788"/>
        <source>No config selected</source>
        <translation>Keine Konfiguration ausgewählt</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="794"/>
        <source>Please Confirm</source>
        <translation>Bitte bestätigen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="795"/>
        <source>Are you sure you want to delete </source>
        <translation>Möchten Sie das wirklich löschen </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="795"/>
        <source>This action cannot be undone</source>
        <translation>Dieser Vorgang kann nicht rückgängig gemacht werden</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="826"/>
        <source>No btrfs subvolumes found</source>
        <translation>Es wurden keine Btrfs-Teilvolumen gefunden</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="852"/>
        <source>Failed to save changes</source>
        <translation>Änderungen speichern fehlgeschlagen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="871"/>
        <source>Changes saved</source>
        <translation>Änderungen gespeichert</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="884"/>
        <source>Please enter a valid name</source>
        <translation>Bitte gültigen Namen eingeben</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="890"/>
        <source>That name is already in use!</source>
        <translation>Dieser Name ist bereits vergeben!</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="921"/>
        <location filename="../src/ui/MainWindow.cpp" line="979"/>
        <location filename="../src/ui/MainWindow.cpp" line="983"/>
        <location filename="../src/ui/MainWindow.cpp" line="1004"/>
        <location filename="../src/ui/MainWindow.cpp" line="1006"/>
        <location filename="../src/ui/MainWindow.cpp" line="1106"/>
        <source>Btrfs Assistant</source>
        <translation>Btrfs Assistant</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="921"/>
        <location filename="../src/ui/MainWindow.cpp" line="979"/>
        <location filename="../src/ui/MainWindow.cpp" line="1106"/>
        <source>Changes applied</source>
        <translation>Änderungen übernommen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="956"/>
        <source>Are you sure you want to set read-only flag for %1?</source>
        <translation>Möchtest du wirklich das Lese-Flag für %1 setzen?</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="958"/>
        <source>Are you sure you want to clear read-only flag for %1?</source>
        <translation>Möchtest du das Lese-Flag für %1 wirklich aufheben?</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="962"/>
        <source>Are you sure you want to set read-only flag for %1 subvolumes?</source>
        <translation>Möchtest du wirklich das Lese-Flag für die %1-Teilvolumen setzen?</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="964"/>
        <source>Are you sure you want to clear read-only flag for %1 subvolumes?</source>
        <translation>Möchtest du das Lese-Flag für die %1-Teilvolumen wirklich aufheben?</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="574"/>
        <location filename="../src/ui/MainWindow.cpp" line="967"/>
        <location filename="../src/ui/MainWindow.cpp" line="1153"/>
        <location filename="../src/ui/MainWindow.cpp" line="1358"/>
        <location filename="../src/ui/MainWindow.cpp" line="1530"/>
        <source>Confirm</source>
        <translation>Bestätigen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="149"/>
        <location filename="../src/ui/MainWindow.cpp" line="173"/>
        <location filename="../src/ui/MainWindow.cpp" line="735"/>
        <location filename="../src/ui/MainWindow.cpp" line="758"/>
        <source>Stop</source>
        <translation>Stopp</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="158"/>
        <source>No balance running.</source>
        <translation>Es wird kein Ausgleich geführt.</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="220"/>
        <source>none</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="220"/>
        <source>daily</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="220"/>
        <source>weekly</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="220"/>
        <source>monthly</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="656"/>
        <source>New Config</source>
        <translation>Neue Konfiguration</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="656"/>
        <source>Cancel New Config</source>
        <translation>Neue Konfiguration abbrechen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="984"/>
        <source>Failed to apply changes to the following subvolumes:</source>
        <translation>Änderungen konnten auf die folgenden Teilvolumen nicht angewendet werden:</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="993"/>
        <source>Create &amp;snapshot...</source>
        <translation>Erstellen &amp;Snapshot...</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1004"/>
        <source>Snapshot created</source>
        <translation>Snapshot erstellen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1011"/>
        <source>Browse subvolume...</source>
        <translation>Teilvolumen durchsuchen...</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1015"/>
        <source>Restore backup...</source>
        <translation>Sicherung wiederherstellen...</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1020"/>
        <source>Set &amp;read-only flag</source>
        <translation>Festlegen &amp;Nur Lesen-Flag</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1026"/>
        <source>&amp;Clear read-only flag</source>
        <translation>&amp;Nur Lesen-Flag löschen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1031"/>
        <source>&amp;Delete</source>
        <translation>&amp;Löschen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1042"/>
        <source>Set cleanup algorithm to &amp;timeline</source>
        <translation>Algorithmus zur Bereinigung auf &amp;Zeitleite setzen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1045"/>
        <source>Set cleanup algorithm to &amp;number</source>
        <translation>Algorithmus zur Bereinigung auf &amp;Nummer festlegen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1048"/>
        <source>&amp;Remove cleanup algorithm</source>
        <translation>&amp;Algorithmus zum Entfernen von Bereinigungsdaten</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1051"/>
        <source>&amp;Delete snapshot</source>
        <translation>&amp;Snapshot löschen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1054"/>
        <source>&amp;Change description</source>
        <translation>&amp;Beschreibung ändern</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1148"/>
        <source>Please select a subvolume to delete first!</source>
        <translation>Bitte wähle zunächst ein Untervolume aus, das gelöscht werden soll!</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1153"/>
        <source>Are you sure you want to delete the selected subvolume(s)?</source>
        <translation>Möchtest du die ausgewählten Teilvolumen wirklich löschen?</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1171"/>
        <source>Snapper Snapshots Found</source>
        <translation>Snapper Snapshots gefunden</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1172"/>
        <source>One or more of the selected subvolumes is a Snapper snapshot, would you like to remove the Snapper Metadata?(Recommended)</source>
        <translation>Mindestens eines der ausgewählten Teilvolumen ist ein Snapper-Snapshot. Möchtest du die Snapper-Metadaten entfernen? (Empfohlen)</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1194"/>
        <source>Failed to delete subvolume!</source>
        <translation>Löschen des Teilvolumens fehlgeschlagen!</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1194"/>
        <source>Invalid subvolume ID</source>
        <translation>Ungültige Teilvolumen-ID</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1200"/>
        <source>You cannot delete mounted subvolume: </source>
        <translation>Du kannst das eingehängte Teilvolumen nicht löschen: </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1201"/>
        <source>Please unmount the subvolume before deleting</source>
        <translation>Bitte hebe die Einbindung des Teilvolumens auf, bevor du es löschst.</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1206"/>
        <source>Failed to delete subvolume </source>
        <translation>删除子卷失败：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1242"/>
        <location filename="../src/ui/MainWindow.cpp" line="1346"/>
        <location filename="../src/ui/MainWindow.cpp" line="1395"/>
        <location filename="../src/ui/MainWindow.cpp" line="1494"/>
        <location filename="../src/ui/MainWindow.cpp" line="1556"/>
        <source>Nothing selected!</source>
        <translation>Nichts ausgewählt!</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1255"/>
        <source>Failed to restore snapshot</source>
        <translation>Snapshots wiederherstellen fehlgeschlagen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1284"/>
        <source>Failed to find snapshot to browse</source>
        <translation>Kein Snapshot zum Durchsuchen gefunden.</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1310"/>
        <source>No config selected for snapshot</source>
        <translation>Keine Konfiguration für den Snapshot ausgewählt</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1316"/>
        <source>Enter a description for the snapshot</source>
        <translation>Gebe eine Beschreibung für den Snapshot ein</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1316"/>
        <source>Description:</source>
        <translation>Beschreibung: </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1358"/>
        <source>Are you sure you want to delete the selected snapshot(s)?</source>
        <translation>Sicher, dass du den/die ausgewählten Snapshot(s) löschen möchtest?</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1367"/>
        <source>Snapshot löschen nicht möglich</source>
        <translation>无法删除快照</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1419"/>
        <source>Change description</source>
        <translation>Beschreibung ändern</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1420"/>
        <source>Changing &lt;u&gt;&lt;b&gt;%1&lt;/b&gt;&lt;/u&gt; snapshot(s) &lt;br&gt;&lt;br&gt;Enter a new description for the snapshot(s):</source>
        <translation>Ändern von &lt;u&gt;&lt;b&gt;%1&lt;/b&gt;&lt;/u&gt; Snapshot(s) &lt;br&gt;&lt;br&gt;Gebe eine neue Beschreibung für den/die Snapshot(s) ein: </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1431"/>
        <source>Cannot change description of snapshot</source>
        <translation>Beschreibung des Snapshots kann nicht geändert werden</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1503"/>
        <source>Please select a single backup subvolume to restore!</source>
        <translation>Bitte wähle ein einzelnes Sicherungs-Teilvolumen zur Wiederherstellung aus!</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1514"/>
        <source>The subvolume you selected is not a Btrfs Assistant backup</source>
        <translation>Das von dir ausgewählte Teilvolumen ist keine Btrfs-Assistant-Sicherung</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1525"/>
        <source>The subvolume is missing!</source>
        <translation>Das Teilvolumen fehlt!</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1530"/>
        <source>Are you sure you want to restore the selected backup?</source>
        <translation>Sicher, dass du die ausgewählte Sicherung wiederherstellen möchtest?</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1543"/>
        <source>Backup Restore</source>
        <translation>Sicherung wiederherstellen</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1544"/>
        <source>Backup restoration complete.</source>
        <translation>Sicherung wiederherstellen fertiggestellt</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1572"/>
        <source>Failed to set cleanup algorithm for snapshot %1</source>
        <translation>Bereinigungsalgorithmus für Snapshot %1 konnte nicht festgelegt werden</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1591"/>
        <source>Disable Btrfs Quotas</source>
        <translation>Btrfs-Kontingente deaktivieren</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1593"/>
        <source>Enable Btrfs Quotas</source>
        <translation>Btrfs-Kontingente aktivieren</translation>
    </message>
</context>
<context>
    <name>RestoreConfirmDialog</name>
    <message>
        <location filename="../src/ui/RestoreConfirmDialog.ui" line="14"/>
        <source>Dialog</source>
        <translation>Dialog</translation>
    </message>
    <message>
        <location filename="../src/ui/RestoreConfirmDialog.ui" line="42"/>
        <source>Name for saved backup(Optional): </source>
        <translation>Name für die gespeicherte Sicherung (optional): </translation>
    </message>
    <message>
        <location filename="../src/ui/RestoreConfirmDialog.ui" line="83"/>
        <source>Yes</source>
        <translation>Ja</translation>
    </message>
    <message>
        <location filename="../src/ui/RestoreConfirmDialog.ui" line="90"/>
        <source>No</source>
        <translation>Nein</translation>
    </message>
    <message>
        <location filename="../src/ui/RestoreConfirmDialog.ui" line="93"/>
        <source>Ctrl+R</source>
        <translation>Ctrl+R</translation>
    </message>
</context>
<context>
    <name>Snapper</name>
    <message>
        <location filename="../src/util/Snapper.cpp" line="359"/>
        <source>Failed to reset ownership of restored file</source>
        <translation>Fehler beim Zurücksetzen der Besitzrechte der wiederhergestellten Datei</translation>
    </message>
    <message>
        <location filename="../src/util/Snapper.cpp" line="388"/>
        <source>Failed to set config</source>
        <translation>Konfiguration festlegen nicht möglich</translation>
    </message>
</context>
<context>
    <name>SnapshotSubvolumeDialog</name>
    <message>
        <location filename="../src/ui/SnapshotSubvolumeDialog.ui" line="14"/>
        <source>Create a snapshot</source>
        <translation>Snapshot erstellen</translation>
    </message>
    <message>
        <location filename="../src/ui/SnapshotSubvolumeDialog.ui" line="20"/>
        <source>Destination:</source>
        <translation>Ziel: </translation>
    </message>
    <message>
        <location filename="../src/ui/SnapshotSubvolumeDialog.ui" line="29"/>
        <source>A filesystem path</source>
        <translation>Ein Dateisystempfad</translation>
    </message>
    <message>
        <location filename="../src/ui/SnapshotSubvolumeDialog.ui" line="42"/>
        <source>Browse...</source>
        <translation>Durchsuchen...</translation>
    </message>
    <message>
        <location filename="../src/ui/SnapshotSubvolumeDialog.ui" line="51"/>
        <source>Read-only</source>
        <translation>Nur Lesen</translation>
    </message>
    <message>
        <location filename="../src/ui/SnapshotSubvolumeDialog.cpp" line="15"/>
        <source>Select a parent directory</source>
        <translation>Übergeordnetes Verzeichnis auswählen</translation>
    </message>
    <message>
        <location filename="../src/ui/SnapshotSubvolumeDialog.cpp" line="24"/>
        <location filename="../src/ui/SnapshotSubvolumeDialog.cpp" line="30"/>
        <source>Btrfs Assistant</source>
        <translation>Btrfs Assistant</translation>
    </message>
    <message>
        <location filename="../src/ui/SnapshotSubvolumeDialog.cpp" line="24"/>
        <source>The destination path cannot be empty</source>
        <translation>Zielpfad darf nicht leer sein</translation>
    </message>
    <message>
        <location filename="../src/ui/SnapshotSubvolumeDialog.cpp" line="31"/>
        <source>You entered a relative path. Do you want to continue with the resulting absolute path: %1?</source>
        <translation>Du hast einen relativen Pfad eingegeben. Möchtest du mit dem daraus resultierenden absoluten Pfad fortfahren: %1?</translation>
    </message>
</context>
<context>
    <name>SubvolumeModel</name>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="16"/>
        <source>Parent ID</source>
        <translation>Übergeordnete ID</translation>
    </message>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="18"/>
        <source>Subvol ID</source>
        <translation>Teilvolumen-ID</translation>
    </message>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="20"/>
        <source>Subvolume</source>
        <translation>Teilvolumen</translation>
    </message>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="22"/>
        <source>UUID</source>
        <translation>UUID</translation>
    </message>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="24"/>
        <source>Parent UUID</source>
        <translation>Übergeordnete UUID</translation>
    </message>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="26"/>
        <source>Received UUID</source>
        <translation>Empfangene UUID</translation>
    </message>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="28"/>
        <source>Created</source>
        <translation>Erstellt</translation>
    </message>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="30"/>
        <source>Generation</source>
        <translation>Generieren</translation>
    </message>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="32"/>
        <source>Read-only</source>
        <translation>Nur Lesen</translation>
    </message>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="34"/>
        <source>Size</source>
        <translation>Größe</translation>
    </message>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="36"/>
        <source>Filesystem</source>
        <translation>Dateisystem</translation>
    </message>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="38"/>
        <source>Exclusive</source>
        <translation>Exklusiv</translation>
    </message>
</context>
<context>
    <name>main</name>
    <message>
        <location filename="../src/main.cpp" line="15"/>
        <source>Btrfs Assistant</source>
        <translation>Btrfs Assistant</translation>
    </message>
    <message>
        <location filename="../src/main.cpp" line="22"/>
        <source>An application for managing Btrfs and Snapper</source>
        <translation>Anwendung zur Verwaltung von Btrfs und Snapper</translation>
    </message>
    <message>
        <location filename="../src/main.cpp" line="28"/>
        <source>List snapshots</source>
        <translation>Snapshots-Liste</translation>
    </message>
    <message>
        <location filename="../src/main.cpp" line="33"/>
        <source>Restore the given snapshot</source>
        <translation>Aangegebene Snapshot wiederherstellen</translation>
    </message>
    <message>
        <location filename="../src/main.cpp" line="34"/>
        <source>index of snapshot</source>
        <translation>Index des Snapshots</translation>
    </message>
    <message>
        <location filename="../src/main.cpp" line="42"/>
        <source>Error: No Btrfs filesystems found</source>
        <translation>Fehler: Keine Btrfs-Dateisysteme gefunden</translation>
    </message>
    <message>
        <location filename="../src/main.cpp" line="64"/>
        <source>Warning: No translations available</source>
        <translation>Warnung: Keine Übersetzungen verfügbar</translation>
    </message>
</context>
</TS>
