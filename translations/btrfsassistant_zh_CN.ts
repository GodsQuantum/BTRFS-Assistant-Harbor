<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.1" language="zh_CN">
<context>
    <name>Btrfs</name>
    <message>
        <location filename="../src/util/Btrfs.cpp" line="115"/>
        <source>Failed to create the snapshot</source>
        <translation>创建快照失败</translation>
    </message>
    <message>
        <location filename="../src/util/Btrfs.cpp" line="380"/>
        <source>You cannot restore to the root of the partition</source>
        <translation>无法恢复到分区根目录</translation>
    </message>
    <message>
        <location filename="../src/util/Btrfs.cpp" line="407"/>
        <source>Failed to make a backup of target subvolume</source>
        <translation>备份目标子卷失败</translation>
    </message>
    <message>
        <location filename="../src/util/Btrfs.cpp" line="428"/>
        <source>Failed to restore subvolume!</source>
        <translation>恢复子卷失败！</translation>
    </message>
    <message>
        <location filename="../src/util/Btrfs.cpp" line="429"/>
        <source>Snapshot restore failed.  Please verify the status of your system before rebooting</source>
        <translation>快照恢复失败。请在重启前确认系统状态</translation>
    </message>
    <message>
        <location filename="../src/util/Btrfs.cpp" line="444"/>
        <source>The restore was successful but the migration of the nested subvolumes failed</source>
        <translation>恢复成功，但嵌套子卷迁移失败</translation>
    </message>
    <message>
        <location filename="../src/util/Btrfs.cpp" line="445"/>
        <source>Please migrate the those subvolumes manually</source>
        <translation>请手动迁移这些子卷</translation>
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
        <translation>无可用统计信息</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="19"/>
        <source>no errors found</source>
        <translation>未发现错误</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="22"/>
        <source>running</source>
        <translation>正在运行</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="25"/>
        <source>finished</source>
        <translation>已完成</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="28"/>
        <source>canceled</source>
        <translation>已取消</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="31"/>
        <source>aborted</source>
        <translation>已中止</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="34"/>
        <source>interrupted</source>
        <translation>已中断</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="64"/>
        <source>UUID:</source>
        <translation>UUID：</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="65"/>
        <source>Scrub started:</source>
        <translation>校验（Scrub）开始时间：</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="66"/>
        <source>Scrub resumed:</source>
        <translation>校验（Scrub）恢复时间：</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="67"/>
        <source>Status:</source>
        <translation>状态：</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="68"/>
        <source>Duration:</source>
        <translation>持续时间：</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="69"/>
        <source>Time left:</source>
        <translation>剩余时间：</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="70"/>
        <source>ETA:</source>
        <translation>预计完成时间：</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="71"/>
        <source>Total to scrub:</source>
        <translation>待校验总量：</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="72"/>
        <source>Bytes scrubbed:</source>
        <translation>已校验数据量：</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="73"/>
        <source>Rate:</source>
        <translation>速率：</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="74"/>
        <source>Error summary:</source>
        <translation>错误摘要：</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="75"/>
        <source>read_errors:</source>
        <translation>读取错误：</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="76"/>
        <source>csum_errors:</source>
        <translation>校验和错误：</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="77"/>
        <source>verify_errors:</source>
        <translation>验证错误：</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="78"/>
        <source>super_errors:</source>
        <translation>超级块错误：</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="79"/>
        <source>malloc_errors:</source>
        <translation>内存分配错误：</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="80"/>
        <source>uncorrectable_errors:</source>
        <translation>不可修复错误：</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="81"/>
        <source>unverified_errors:</source>
        <translation>未验证错误：</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="111"/>
        <source>No balance operation found on %1</source>
        <translation>“%1”上没有正在运行的均衡（Balance）操作</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="116"/>
        <source>Balance operation on %1 is running</source>
        <translation>“%1”上的均衡（Balance）正在运行</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="121"/>
        <source>Balance operation on %1 is paused</source>
        <translation>“%1”上的均衡（Balance）已暂停</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="126"/>
        <source>Done, relocated %1 of %2 chunks</source>
        <translation>已完成，重定位了 %1/%2 个区块</translation>
    </message>
    <message>
        <location filename="../src/util/BtrfsStatus.cpp" line="131"/>
        <source>%1 of about %2 chunks balanced (%3 considered), %4% left</source>
        <translation>已完成约 %2 个区块中的 %1 个均衡（Balance）（已检查 %3 个），剩余 %4%</translation>
    </message>
</context>
<context>
    <name>Cli</name>
    <message>
        <location filename="../src/ui/Cli.cpp" line="34"/>
        <location filename="../src/ui/Cli.cpp" line="52"/>
        <source>You must run this application as root</source>
        <translation>必须以 root 身份运行此应用程序</translation>
    </message>
    <message>
        <location filename="../src/ui/Cli.cpp" line="61"/>
        <source>Failed to parse snapshot list</source>
        <translation>解析快照列表失败</translation>
    </message>
    <message>
        <location filename="../src/ui/Cli.cpp" line="69"/>
        <source>This is not a snapshot that can be restored by this application</source>
        <translation>此快照无法由本应用程序恢复</translation>
    </message>
    <message>
        <location filename="../src/ui/Cli.cpp" line="78"/>
        <source>Source snapshot not found</source>
        <translation>未找到源快照</translation>
    </message>
    <message>
        <location filename="../src/ui/Cli.cpp" line="83"/>
        <source>Snapshot subvolume not found</source>
        <translation>未找到快照子卷</translation>
    </message>
    <message>
        <location filename="../src/ui/Cli.cpp" line="92"/>
        <source>Target not found</source>
        <translation>未找到目标</translation>
    </message>
    <message>
        <location filename="../src/ui/Cli.cpp" line="96"/>
        <source>Restoring snapshot %1</source>
        <translation>正在恢复快照 %1</translation>
    </message>
    <message>
        <location filename="../src/ui/Cli.cpp" line="103"/>
        <source>Snapshot restoration complete.</source>
        <translation>快照恢复完成。</translation>
    </message>
    <message>
        <location filename="../src/ui/Cli.cpp" line="104"/>
        <source>A copy of the original subvolume has been saved as </source>
        <translation>原始子卷的副本已保存为：</translation>
    </message>
    <message>
        <location filename="../src/ui/Cli.cpp" line="105"/>
        <source>Please reboot immediately
</source>
        <translation>请立即重启
</translation>
    </message>
</context>
<context>
    <name>DiffViewer</name>
    <message>
        <location filename="../src/ui/DiffViewer.ui" line="14"/>
        <source>Dialog</source>
        <translation>对话框</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.ui" line="83"/>
        <source>Select a snapshot from the left to see the diff</source>
        <translation>从左侧选择快照以查看差异</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.ui" line="116"/>
        <source>Restore</source>
        <translation>恢复</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.ui" line="123"/>
        <source>Close</source>
        <translation>关闭</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="14"/>
        <source>Diff Viewer</source>
        <translation>差异查看器</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="29"/>
        <source>Confirm</source>
        <translation>确认</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="29"/>
        <source>Are you sure you want to restore this the file over the current file?</source>
        <translation>确定要用此文件覆盖当前文件吗？</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="38"/>
        <source>Restore Failed</source>
        <translation>恢复失败</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="38"/>
        <source>The file failed to restore</source>
        <translation>文件恢复失败</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="42"/>
        <source>Restore File</source>
        <translation>恢复文件</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="42"/>
        <source>The file was successfully restored</source>
        <translation>文件恢复成功</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="63"/>
        <source>Num</source>
        <comment>The number associated with a snapshot</comment>
        <translation>编号</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="64"/>
        <source>Date/Time</source>
        <translation>日期/时间</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="65"/>
        <source>Root Path</source>
        <translation>根路径</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="66"/>
        <source>File Path</source>
        <translation>文件路径</translation>
    </message>
    <message>
        <location filename="../src/ui/DiffViewer.cpp" line="121"/>
        <source>There are no differences between the selected files</source>
        <translation>所选文件之间没有差异</translation>
    </message>
</context>
<context>
    <name>FileBrowser</name>
    <message>
        <location filename="../src/ui/FileBrowser.ui" line="14"/>
        <source>Dialog</source>
        <translation>对话框</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.ui" line="70"/>
        <source>Show Diff</source>
        <translation>显示差异</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.ui" line="83"/>
        <location filename="../src/ui/FileBrowser.cpp" line="93"/>
        <location filename="../src/ui/FileBrowser.cpp" line="113"/>
        <source>Restore File</source>
        <translation>恢复文件</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.ui" line="96"/>
        <source>Close</source>
        <translation>关闭</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.cpp" line="41"/>
        <source>Snapshot File Viewer</source>
        <translation>快照文件查看器</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.cpp" line="53"/>
        <source>File Viewer</source>
        <translation>文件查看器</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.cpp" line="70"/>
        <source>Diff File</source>
        <translation>比较文件</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.cpp" line="71"/>
        <source> is a directory, only files can be diffed</source>
        <translation> 是目录，只能比较文件</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.cpp" line="94"/>
        <source> is a directory, only files can be restored</source>
        <translation> 是目录，只能恢复文件</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.cpp" line="98"/>
        <source>Confirm</source>
        <translation>确认</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.cpp" line="98"/>
        <source>Are you sure you want to restore this the file over the current file?</source>
        <translation>确定要用此文件覆盖当前文件吗？</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.cpp" line="109"/>
        <source>Restore Failed</source>
        <translation>恢复失败</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.cpp" line="109"/>
        <source>The file failed to restore</source>
        <translation>文件恢复失败</translation>
    </message>
    <message>
        <location filename="../src/ui/FileBrowser.cpp" line="113"/>
        <source>The file was successfully restored</source>
        <translation>文件恢复成功</translation>
    </message>
</context>
<context>
    <name>MainWindow</name>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="14"/>
        <source>BTRFS-Assistant</source>
        <translation>Btrfs 助手</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="31"/>
        <source>Overview</source>
        <translation>概览</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="67"/>
        <location filename="../src/ui/MainWindow.ui" line="1577"/>
        <source>Scrub</source>
        <translation>校验（Scrub）</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="108"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Perform scrub on device.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;对设备执行校验（Scrub）。&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="111"/>
        <location filename="../src/ui/MainWindow.ui" line="195"/>
        <location filename="../src/ui/MainWindow.cpp" line="159"/>
        <location filename="../src/ui/MainWindow.cpp" line="179"/>
        <source>Start</source>
        <translation>开始</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="126"/>
        <source>No scrub ran.</source>
        <translation>尚未执行校验（Scrub）。</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="151"/>
        <location filename="../src/ui/MainWindow.ui" line="1503"/>
        <source>Balance</source>
        <translation>均衡（Balance）</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="192"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Perform full balance on device.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;对设备执行完整均衡（Balance）。&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="214"/>
        <source>No balance ran.</source>
        <translation>尚未执行均衡（Balance）。</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="236"/>
        <source>Internal Filesystem Statistics</source>
        <translation>内部文件系统统计</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="242"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Utilization percentage of system chunks in the allocated space.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;已分配空间中系统区块的利用率。&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="252"/>
        <source>Data:</source>
        <translation>数据：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="259"/>
        <source>Metadata:</source>
        <translation>元数据：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="266"/>
        <source>System:</source>
        <translation>系统：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="273"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Utilization percentage of metadata chunks in the allocated space.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;已分配空间中元数据区块的利用率。&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="283"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Utilization percentage of file data chunks in the allocated space.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;已分配空间中文件数据区块的利用率。&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="302"/>
        <source>Information</source>
        <translation>信息</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="308"/>
        <source>Used:</source>
        <translation>已用：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="315"/>
        <location filename="../src/ui/MainWindow.ui" line="392"/>
        <source>Estimate of the amount of data that can still be written to this FS, based on the current usage profile.</source>
        <translation>根据当前使用配置估算仍可写入此文件系统的数据量。</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="325"/>
        <location filename="../src/ui/MainWindow.ui" line="402"/>
        <source>Minimum amount of data that you can expect to be able to get onto the filesystem. </source>
        <translation>预计至少还能写入文件系统的数据量。</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="345"/>
        <source>Allocated:  </source>
        <translation>已分配：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="359"/>
        <source>Filesystem Size: </source>
        <translation>文件系统大小：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="395"/>
        <source>Free (Estimated): </source>
        <translation>可用（估算）：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="405"/>
        <source>Free (Minimum): </source>
        <translation>可用（最低）：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="421"/>
        <source>Volume Selection</source>
        <translation>卷选择</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="427"/>
        <source>Filesystem:</source>
        <translation>文件系统：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="463"/>
        <source>Enable Quotas</source>
        <translation>启用配额</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="470"/>
        <source>Refresh Btrfs Data</source>
        <translation>刷新 Btrfs 数据</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="485"/>
        <source>Subvolumes</source>
        <translation>子卷</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="523"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Include children subvolumes of .snapshots and timeshift folders.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;包含 .snapshots 和 timeshift 目录下的子卷。&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="526"/>
        <source>Include Timeshift and Snapper Snapshots</source>
        <translation>包含 Timeshift 和 Snapper 快照</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="536"/>
        <source>Include Container Subvolumes</source>
        <translation>包含容器子卷</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="557"/>
        <source>Filter...</source>
        <translation>筛选...</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="583"/>
        <source>Restore Backup</source>
        <translation>恢复备份</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="603"/>
        <location filename="../src/ui/MainWindow.ui" line="905"/>
        <source>Browse</source>
        <translation>浏览</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="623"/>
        <location filename="../src/ui/MainWindow.ui" line="786"/>
        <location filename="../src/ui/MainWindow.ui" line="1070"/>
        <source>Delete</source>
        <translation>删除</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="643"/>
        <location filename="../src/ui/MainWindow.ui" line="812"/>
        <location filename="../src/ui/MainWindow.ui" line="951"/>
        <source>Refresh</source>
        <translation>刷新</translation>
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
        <translation>新建/删除</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="733"/>
        <location filename="../src/ui/MainWindow.ui" line="1040"/>
        <source>Select config: </source>
        <translation>选择配置：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="766"/>
        <location filename="../src/ui/MainWindow.ui" line="1063"/>
        <source>New</source>
        <translation>新建</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="849"/>
        <source>Browse/Restore</source>
        <translation>浏览/恢复</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="870"/>
        <source>Select target: </source>
        <translation>选择目标：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="925"/>
        <source>Restore</source>
        <translation>恢复</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="992"/>
        <source>Snapper Settings</source>
        <translation>Snapper 设置</translation>
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
        <translation>配置信息</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1106"/>
        <location filename="../src/ui/MainWindow.ui" line="1169"/>
        <source>Config name: </source>
        <translation>配置名称：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1133"/>
        <location filename="../src/ui/MainWindow.ui" line="1196"/>
        <source>Backup path: </source>
        <translation>备份路径：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1232"/>
        <source>Snapshot Retention</source>
        <translation>快照保留策略</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1238"/>
        <location filename="../src/ui/MainWindow.ui" line="1261"/>
        <location filename="../src/ui/MainWindow.ui" line="1275"/>
        <location filename="../src/ui/MainWindow.ui" line="1282"/>
        <location filename="../src/ui/MainWindow.ui" line="1353"/>
        <source>Save: </source>
        <translation>保留：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1251"/>
        <location filename="../src/ui/MainWindow.ui" line="1289"/>
        <source>Timeline snapshots are taken hourly, the cleanup job reduces the snapshots in accordance with the below settings</source>
        <translation>时间线快照每小时创建一次，清理任务会根据以下设置减少快照数量</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1254"/>
        <source>Enable timeline snapshots</source>
        <translation>启用时间线快照</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1268"/>
        <source>Daily</source>
        <translation>每日</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1308"/>
        <source>Yearly</source>
        <translation>每年</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1315"/>
        <source>Monthly</source>
        <translation>每月</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1325"/>
        <source>Hourly</source>
        <translation>每小时</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1332"/>
        <source>Weekly</source>
        <translation>每周</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1339"/>
        <source>Save:</source>
        <translation>保留：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1346"/>
        <source>Number</source>
        <translation>数量</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1382"/>
        <source>systemd Unit Settings</source>
        <translation>systemd 单元设置</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1388"/>
        <source>Snapper timeline enabled</source>
        <translation>启用 Snapper 时间线</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1401"/>
        <source>Snapper cleanup enabled</source>
        <translation>启用 Snapper 清理</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1414"/>
        <source>Snapper boot enabled</source>
        <translation>启用 Snapper 启动快照</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1433"/>
        <source>Apply systemd changes</source>
        <translation>应用 systemd 更改</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1461"/>
        <source>Btrfs maintenance</source>
        <translation>Btrfs 维护</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1531"/>
        <location filename="../src/ui/MainWindow.ui" line="1621"/>
        <location filename="../src/ui/MainWindow.ui" line="1695"/>
        <source>Frequency: </source>
        <translation>频率：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1541"/>
        <location filename="../src/ui/MainWindow.ui" line="1628"/>
        <location filename="../src/ui/MainWindow.ui" line="1702"/>
        <source>Select All</source>
        <translation>全选</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1548"/>
        <location filename="../src/ui/MainWindow.ui" line="1635"/>
        <location filename="../src/ui/MainWindow.ui" line="1709"/>
        <source>Mountpoints: </source>
        <translation>挂载点：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1651"/>
        <source>Defrag</source>
        <translation>碎片整理</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1747"/>
        <source>Reset</source>
        <translation>重置</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1767"/>
        <source>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;Update Btrfs Maintenance config file and call service to load new settings.&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</source>
        <translation>&lt;html&gt;&lt;head/&gt;&lt;body&gt;&lt;p&gt;更新 Btrfs Maintenance 配置文件，并调用服务加载新设置。&lt;/p&gt;&lt;/body&gt;&lt;/html&gt;</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.ui" line="1770"/>
        <source>Apply</source>
        <translation>应用</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="59"/>
        <source>The application must be run as the superuser(root)</source>
        <translation>必须以超级用户（root）身份运行此应用程序</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="87"/>
        <source>Error</source>
        <translation>错误</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="318"/>
        <source>You have lots of free space, did you overbuy?</source>
        <translation>可用空间很多，是不是买大了？</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="320"/>
        <source>Situation critical!  Time to delete some data or buy more disk</source>
        <translation>情况危急！该删除一些数据或购买更大的磁盘了</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="322"/>
        <source>Your disk space is well utilized</source>
        <translation>磁盘空间利用率良好</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="374"/>
        <location filename="../src/ui/MainWindow.cpp" line="424"/>
        <source>Number</source>
        <comment>The number associated with a snapshot</comment>
        <translation>编号</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="375"/>
        <location filename="../src/ui/MainWindow.cpp" line="428"/>
        <source>Date/Time</source>
        <translation>日期/时间</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="376"/>
        <location filename="../src/ui/MainWindow.cpp" line="429"/>
        <source>Type</source>
        <translation>类型</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="377"/>
        <source>Cleanup</source>
        <translation>清理策略</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="378"/>
        <location filename="../src/ui/MainWindow.cpp" line="431"/>
        <source>Description</source>
        <translation>描述</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="426"/>
        <source>Subvolume</source>
        <translation>子卷</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="542"/>
        <source>This is not a snapshot that can be restored by this application</source>
        <translation>此快照无法由本应用程序恢复</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="552"/>
        <source>Snapshot subvolume not found</source>
        <translation>未找到快照子卷</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="562"/>
        <source>Target not found</source>
        <translation>未找到目标</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="568"/>
        <source>Warning subvolid mount detected!</source>
        <translation>警告：检测到按 subvolid 挂载！</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="569"/>
        <source>It appears you are currently mounting by subvolid.  Doing a restore in this case may not produce the expected outcome.  It is highly recommended you switch to mounting by subvolume path before proceeding!</source>
        <translation>当前似乎正在按 subvolid 挂载。在这种情况下执行恢复可能无法得到预期结果。强烈建议在继续前改为按子卷路径挂载！</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="574"/>
        <source>Are you sure you want to restore </source>
        <translation>确定要恢复 </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="574"/>
        <source> to </source>
        <comment>as in from/to</comment>
        <translation> 到 </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="588"/>
        <source>Snapshot Restore</source>
        <translation>快照恢复</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="589"/>
        <source>Snapshot restoration complete.</source>
        <translation>快照恢复完成。</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="589"/>
        <location filename="../src/ui/MainWindow.cpp" line="1544"/>
        <source>A copy of the original subvolume has been saved as </source>
        <translation>原始子卷的副本已保存为：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="590"/>
        <location filename="../src/ui/MainWindow.cpp" line="1545"/>
        <source>Please reboot immediately</source>
        <translation>请立即重启</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="788"/>
        <source>No config selected</source>
        <translation>未选择配置</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="794"/>
        <source>Please Confirm</source>
        <translation>请确认</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="795"/>
        <source>Are you sure you want to delete </source>
        <translation>确定要删除 </translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="795"/>
        <source>This action cannot be undone</source>
        <translation>此操作无法撤销</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="826"/>
        <source>No btrfs subvolumes found</source>
        <translation>未找到 Btrfs 子卷</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="852"/>
        <source>Failed to save changes</source>
        <translation>保存更改失败</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="871"/>
        <source>Changes saved</source>
        <translation>更改已保存</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="884"/>
        <source>Please enter a valid name</source>
        <translation>请输入有效名称</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="890"/>
        <source>That name is already in use!</source>
        <translation>该名称已被使用！</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="921"/>
        <location filename="../src/ui/MainWindow.cpp" line="979"/>
        <location filename="../src/ui/MainWindow.cpp" line="983"/>
        <location filename="../src/ui/MainWindow.cpp" line="1004"/>
        <location filename="../src/ui/MainWindow.cpp" line="1006"/>
        <location filename="../src/ui/MainWindow.cpp" line="1106"/>
        <source>Btrfs Assistant</source>
        <translation>Btrfs 助手</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="921"/>
        <location filename="../src/ui/MainWindow.cpp" line="979"/>
        <location filename="../src/ui/MainWindow.cpp" line="1106"/>
        <source>Changes applied</source>
        <translation>更改已应用</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="956"/>
        <source>Are you sure you want to set read-only flag for %1?</source>
        <translation>确定要为 %1 设置只读标志吗？</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="958"/>
        <source>Are you sure you want to clear read-only flag for %1?</source>
        <translation>确定要清除 %1 的只读标志吗？</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="962"/>
        <source>Are you sure you want to set read-only flag for %1 subvolumes?</source>
        <translation>确定要为 %1 个子卷设置只读标志吗？</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="964"/>
        <source>Are you sure you want to clear read-only flag for %1 subvolumes?</source>
        <translation>确定要清除 %1 个子卷的只读标志吗？</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="574"/>
        <location filename="../src/ui/MainWindow.cpp" line="967"/>
        <location filename="../src/ui/MainWindow.cpp" line="1153"/>
        <location filename="../src/ui/MainWindow.cpp" line="1358"/>
        <location filename="../src/ui/MainWindow.cpp" line="1530"/>
        <source>Confirm</source>
        <translation>确认</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="149"/>
        <location filename="../src/ui/MainWindow.cpp" line="173"/>
        <location filename="../src/ui/MainWindow.cpp" line="735"/>
        <location filename="../src/ui/MainWindow.cpp" line="758"/>
        <source>Stop</source>
        <translation>停止</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="158"/>
        <source>No balance running.</source>
        <translation>当前没有正在运行的均衡（Balance）操作。</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="220"/>
        <source>none</source>
        <translation>无</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="220"/>
        <source>daily</source>
        <translation>每天</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="220"/>
        <source>weekly</source>
        <translation>每周</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="220"/>
        <source>monthly</source>
        <translation>每月</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="656"/>
        <source>New Config</source>
        <translation>新建配置</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="656"/>
        <source>Cancel New Config</source>
        <translation>取消新建配置</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="984"/>
        <source>Failed to apply changes to the following subvolumes:</source>
        <translation>无法将更改应用到以下子卷：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="993"/>
        <source>Create &amp;snapshot...</source>
        <translation>创建快照(&amp;S)...</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1004"/>
        <source>Snapshot created</source>
        <translation>快照已创建</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1011"/>
        <source>Browse subvolume...</source>
        <translation>浏览子卷...</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1015"/>
        <source>Restore backup...</source>
        <translation>恢复备份...</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1020"/>
        <source>Set &amp;read-only flag</source>
        <translation>设置只读标志(&amp;R)</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1026"/>
        <source>&amp;Clear read-only flag</source>
        <translation>清除只读标志(&amp;C)</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1031"/>
        <source>&amp;Delete</source>
        <translation>删除(&amp;D)</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1042"/>
        <source>Set cleanup algorithm to &amp;timeline</source>
        <translation>将清理算法设为时间线(&amp;T)</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1045"/>
        <source>Set cleanup algorithm to &amp;number</source>
        <translation>将清理算法设为数量(&amp;N)</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1048"/>
        <source>&amp;Remove cleanup algorithm</source>
        <translation>移除清理算法(&amp;R)</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1051"/>
        <source>&amp;Delete snapshot</source>
        <translation>删除快照(&amp;D)</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1054"/>
        <source>&amp;Change description</source>
        <translation>更改描述(&amp;C)</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1148"/>
        <source>Please select a subvolume to delete first!</source>
        <translation>请先选择要删除的子卷！</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1153"/>
        <source>Are you sure you want to delete the selected subvolume(s)?</source>
        <translation>确定要删除所选子卷吗？</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1171"/>
        <source>Snapper Snapshots Found</source>
        <translation>发现 Snapper 快照</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1172"/>
        <source>One or more of the selected subvolumes is a Snapper snapshot, would you like to remove the Snapper Metadata?(Recommended)</source>
        <translation>所选子卷中有一个或多个是 Snapper 快照，是否同时移除 Snapper 元数据？（推荐）</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1194"/>
        <source>Failed to delete subvolume!</source>
        <translation>删除子卷失败！</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1194"/>
        <source>Invalid subvolume ID</source>
        <translation>无效的子卷 ID</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1200"/>
        <source>You cannot delete mounted subvolume: </source>
        <translation>无法删除已挂载的子卷：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1201"/>
        <source>Please unmount the subvolume before deleting</source>
        <translation>请先卸载该子卷再删除</translation>
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
        <translation>未选择任何项目！</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1255"/>
        <source>Failed to restore snapshot</source>
        <translation>恢复快照失败</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1284"/>
        <source>Failed to find snapshot to browse</source>
        <translation>找不到要浏览的快照</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1310"/>
        <source>No config selected for snapshot</source>
        <translation>未为快照选择配置</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1316"/>
        <source>Enter a description for the snapshot</source>
        <translation>输入快照描述</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1316"/>
        <source>Description:</source>
        <translation>描述：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1358"/>
        <source>Are you sure you want to delete the selected snapshot(s)?</source>
        <translation>确定要删除所选快照吗？</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1367"/>
        <source>Cannot delete snapshot</source>
        <translation>无法删除快照</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1419"/>
        <source>Change description</source>
        <translation>更改描述</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1420"/>
        <source>Changing &lt;u&gt;&lt;b&gt;%1&lt;/b&gt;&lt;/u&gt; snapshot(s) &lt;br&gt;&lt;br&gt;Enter a new description for the snapshot(s):</source>
        <translation>正在更改 &lt;u&gt;&lt;b&gt;%1&lt;/b&gt;&lt;/u&gt; 个快照&lt;br&gt;&lt;br&gt;请输入新的快照描述：</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1431"/>
        <source>Cannot change description of snapshot</source>
        <translation>无法更改快照描述</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1503"/>
        <source>Please select a single backup subvolume to restore!</source>
        <translation>请选择一个要恢复的备份子卷！</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1514"/>
        <source>The subvolume you selected is not a Btrfs Assistant backup</source>
        <translation>所选子卷不是 Btrfs 助手备份</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1525"/>
        <source>The subvolume is missing!</source>
        <translation>子卷不存在！</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1530"/>
        <source>Are you sure you want to restore the selected backup?</source>
        <translation>确定要恢复所选备份吗？</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1543"/>
        <source>Backup Restore</source>
        <translation>备份恢复</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1544"/>
        <source>Backup restoration complete.</source>
        <translation>备份恢复完成。</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1572"/>
        <source>Failed to set cleanup algorithm for snapshot %1</source>
        <translation>为快照%1 设置清理算法失败</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1591"/>
        <source>Disable Btrfs Quotas</source>
        <translation>禁用 Btrfs 配额</translation>
    </message>
    <message>
        <location filename="../src/ui/MainWindow.cpp" line="1593"/>
        <source>Enable Btrfs Quotas</source>
        <translation>启用 Btrfs 配额</translation>
    </message>
        <message>
            <source>Language</source>
            <translation>语言</translation>
        </message>
            <message>
            <source>Remote backups</source>
            <translation>远程备份</translation>
        </message>
    </context>
<context>
    <name>RestoreConfirmDialog</name>
    <message>
        <location filename="../src/ui/RestoreConfirmDialog.ui" line="14"/>
        <source>Dialog</source>
        <translation>对话框</translation>
    </message>
    <message>
        <location filename="../src/ui/RestoreConfirmDialog.ui" line="42"/>
        <source>Name for saved backup(Optional): </source>
        <translation>保存的备份名称（可选）：</translation>
    </message>
    <message>
        <location filename="../src/ui/RestoreConfirmDialog.ui" line="83"/>
        <source>Yes</source>
        <translation>是</translation>
    </message>
    <message>
        <location filename="../src/ui/RestoreConfirmDialog.ui" line="90"/>
        <source>No</source>
        <translation>否</translation>
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
        <translation>重置已恢复文件的所有权失败</translation>
    </message>
    <message>
        <location filename="../src/util/Snapper.cpp" line="388"/>
        <source>Failed to set config</source>
        <translation>设置配置失败</translation>
    </message>
</context>
<context>
    <name>SnapshotSubvolumeDialog</name>
    <message>
        <location filename="../src/ui/SnapshotSubvolumeDialog.ui" line="14"/>
        <source>Create a snapshot</source>
        <translation>创建快照</translation>
    </message>
    <message>
        <location filename="../src/ui/SnapshotSubvolumeDialog.ui" line="20"/>
        <source>Destination:</source>
        <translation>目标位置：</translation>
    </message>
    <message>
        <location filename="../src/ui/SnapshotSubvolumeDialog.ui" line="29"/>
        <source>A filesystem path</source>
        <translation>文件系统路径</translation>
    </message>
    <message>
        <location filename="../src/ui/SnapshotSubvolumeDialog.ui" line="42"/>
        <source>Browse...</source>
        <translation>浏览...</translation>
    </message>
    <message>
        <location filename="../src/ui/SnapshotSubvolumeDialog.ui" line="51"/>
        <source>Read-only</source>
        <translation>只读</translation>
    </message>
    <message>
        <location filename="../src/ui/SnapshotSubvolumeDialog.cpp" line="15"/>
        <source>Select a parent directory</source>
        <translation>选择父目录</translation>
    </message>
    <message>
        <location filename="../src/ui/SnapshotSubvolumeDialog.cpp" line="24"/>
        <location filename="../src/ui/SnapshotSubvolumeDialog.cpp" line="30"/>
        <source>Btrfs Assistant</source>
        <translation>Btrfs 助手</translation>
    </message>
    <message>
        <location filename="../src/ui/SnapshotSubvolumeDialog.cpp" line="24"/>
        <source>The destination path cannot be empty</source>
        <translation>目标路径不能为空</translation>
    </message>
    <message>
        <location filename="../src/ui/SnapshotSubvolumeDialog.cpp" line="31"/>
        <source>You entered a relative path. Do you want to continue with the resulting absolute path: %1?</source>
        <translation>输入的是相对路径。是否使用生成的绝对路径继续：%1？</translation>
    </message>
</context>
<context>
    <name>SubvolumeModel</name>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="16"/>
        <source>Parent ID</source>
        <translation>父 ID</translation>
    </message>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="18"/>
        <source>Subvol ID</source>
        <translation>子卷 ID</translation>
    </message>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="20"/>
        <source>Subvolume</source>
        <translation>子卷</translation>
    </message>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="22"/>
        <source>UUID</source>
        <translation>UUID</translation>
    </message>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="24"/>
        <source>Parent UUID</source>
        <translation>父 UUID</translation>
    </message>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="26"/>
        <source>Received UUID</source>
        <translation>接收 UUID</translation>
    </message>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="28"/>
        <source>Created</source>
        <translation>创建时间</translation>
    </message>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="30"/>
        <source>Generation</source>
        <translation>世代</translation>
    </message>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="32"/>
        <source>Read-only</source>
        <translation>只读</translation>
    </message>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="34"/>
        <source>Size</source>
        <translation>大小</translation>
    </message>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="36"/>
        <source>Filesystem</source>
        <translation>文件系统</translation>
    </message>
    <message>
        <location filename="../src/model/SubvolModel.cpp" line="38"/>
        <source>Exclusive</source>
        <translation>独占用量</translation>
    </message>
        <message>
            <source>Yes</source>
            <translation>是</translation>
        </message>
        <message>
            <source>No</source>
            <translation>否</translation>
        </message>
    </context>
<context>
    <name>main</name>
    <message>
        <location filename="../src/main.cpp" line="15"/>
        <source>Btrfs Assistant</source>
        <translation>Btrfs 助手</translation>
    </message>
    <message>
        <location filename="../src/main.cpp" line="22"/>
        <source>An application for managing Btrfs and Snapper</source>
        <translation>用于管理 Btrfs 和 Snapper 的应用程序</translation>
    </message>
    <message>
        <location filename="../src/main.cpp" line="28"/>
        <source>List snapshots</source>
        <translation>列出快照</translation>
    </message>
    <message>
        <location filename="../src/main.cpp" line="33"/>
        <source>Restore the given snapshot</source>
        <translation>恢复指定快照</translation>
    </message>
    <message>
        <location filename="../src/main.cpp" line="34"/>
        <source>index of snapshot</source>
        <translation>快照索引</translation>
    </message>
    <message>
        <location filename="../src/main.cpp" line="42"/>
        <source>Error: No Btrfs filesystems found</source>
        <translation>错误：未找到 Btrfs 文件系统</translation>
    </message>
    <message>
        <location filename="../src/main.cpp" line="64"/>
        <source>Warning: No translations available</source>
        <translation>警告：没有可用的翻译</translation>
    </message>
        <message>
            <source>Btrfs Assistant Harbor</source>
            <translation>Btrfs Assistant Harbor</translation>
        </message>
    </context>
    <context>
        <name>RemoteBackupWidget</name>
        <message>
            <source>Allow explicitly selected local destination</source>
            <translation>允许明确选择本地目标目录</translation>
        </message>
        <message>
            <source>Ready: no backup in progress</source>
            <translation>就绪：当前没有备份任务</translation>
        </message>
        <message>
            <source>Send selected snapshot</source>
            <translation>发送所选快照</translation>
        </message>
        <message>
            <source>Cancel current operation</source>
            <translation>取消当前操作</translation>
        </message>
        <message>
            <source>Remote backups — Snapper snapshots</source>
            <translation>远程备份 — Snapper 快照</translation>
        </message>
        <message>
            <source>Snapshots and local rollback remain managed by Snapper. Harbor handles remote transport, verification and retrieval. No Snapper history is recursively copied.</source>
            <translation>快照和本地回滚仍由 Snapper 管理。Harbor 负责远程传输、验证和恢复提取；不会递归复制 Snapper 的历史记录。</translation>
        </message>
        <message>
            <source>Source and destination</source>
            <translation>来源与目标</translation>
        </message>
        <message>
            <source>Refresh snapshots</source>
            <translation>刷新快照</translation>
        </message>
        <message>
            <source>Harbor checkpoint v2 — compatible archives</source>
            <translation>Harbor 检查点 v2 — 兼容旧归档</translation>
        </message>
        <message>
            <source>Harbor CAS — deduplicated backups</source>
            <translation>Harbor CAS — 去重备份</translation>
        </message>
        <message>
            <source>Backup engine</source>
            <translation>备份引擎</translation>
        </message>
        <message>
            <source>Machine identity inside a shared CAS repository (not a sub-repository).</source>
            <translation>共享 CAS 仓库中的机器标识（不是独立的子仓库）。</translation>
        </message>
        <message>
            <source>CAS machine name</source>
            <translation>CAS 机器名称</translation>
        </message>
        <message>
            <source>Snapper configuration</source>
            <translation>Snapper 配置</translation>
        </message>
        <message>
            <source>Readonly snapshot</source>
            <translation>只读快照</translation>
        </message>
        <message>
            <source>Incremental parent (CAS)</source>
            <translation>增量备份的父归档（CAS）</translation>
        </message>
        <message>
            <source>Existing NFS/SMB mount or local backup directory</source>
            <translation>现有 NFS/SMB 挂载点或本地备份目录</translation>
        </message>
        <message>
            <source>Browse</source>
            <translation>浏览</translation>
        </message>
        <message>
            <source>Destination</source>
            <translation>目标目录</translation>
        </message>
        <message>
            <source>Empty Btrfs staging directory for a restored snapshot</source>
            <translation>用于恢复快照的空 Btrfs 暂存目录</translation>
        </message>
        <message>
            <source>Recovery staging</source>
            <translation>恢复暂存目录</translation>
        </message>
        <message>
            <source>Hourly</source>
            <translation>每小时</translation>
        </message>
        <message>
            <source>Daily</source>
            <translation>每天</translation>
        </message>
        <message>
            <source>Weekly</source>
            <translation>每周</translation>
        </message>
        <message>
            <source>Scheduled transfer</source>
            <translation>定时传输</translation>
        </message>
        <message>
            <source>List remote backups</source>
            <translation>列出远程备份</translation>
        </message>
        <message>
            <source>Interrupted transfers</source>
            <translation>中断的传输</translation>
        </message>
        <message>
            <source>Resume selected</source>
            <translation>恢复所选传输</translation>
        </message>
        <message>
            <source>Enable schedule</source>
            <translation>启用定时任务</translation>
        </message>
        <message>
            <source>Disable schedule</source>
            <translation>停用定时任务</translation>
        </message>
        <message>
            <source>Scheduled backups</source>
            <translation>已安排的备份</translation>
        </message>
        <message>
            <source>Initialize CAS destination</source>
            <translation>初始化 CAS 目标目录</translation>
        </message>
        <message>
            <source>Verify selected archive</source>
            <translation>验证所选归档</translation>
        </message>
        <message>
            <source>Delete selected CAS backup</source>
            <translation>删除所选 CAS 备份</translation>
        </message>
        <message>
            <source>Reclaim unused CAS chunks</source>
            <translation>回收未使用的 CAS 数据块</translation>
        </message>
        <message>
            <source>Preview recovery</source>
            <translation>预览恢复</translation>
        </message>
        <message>
            <source>Select a completed archive to verify/recover, or an interrupted transfer to resume</source>
            <translation>选择已完成的归档进行验证或恢复，或选择中断的传输继续执行</translation>
        </message>
        <message>
            <source>Whole-computer backup sets — checkpoint-v2 (QA)</source>
            <translation>整机备份集合 — 检查点 v2（质量测试）</translation>
        </message>
        <message>
            <source>Audit backup coverage</source>
            <translation>审核备份覆盖范围</translation>
        </message>
        <message>
            <source>List machine backup sets</source>
            <translation>列出机器备份集合</translation>
        </message>
        <message>
            <source>Preview staged machine restore</source>
            <translation>预览分阶段的机器恢复</translation>
        </message>
        <message>
            <source>Historical machine sets may include separate Btrfs volumes and EFI files. The preview validates an empty Btrfs staging directory; it never restores the active system or claims the backup is bootable. CAS and checkpoint-v2 repositories have different formats.</source>
            <translation>历史机器备份集合可能包含多个独立的 Btrfs 卷和 EFI 文件。预览仅验证空的 Btrfs 暂存目录；它不会恢复当前运行的系统，也不保证备份可启动。CAS 和检查点 v2 仓库使用不同的格式。</translation>
        </message>
        <message>
            <source>Transfers run asynchronously; process output appears here.</source>
            <translation>传输以异步方式运行；进程输出将显示在此处。</translation>
        </message>
        <message>
            <source>Choose a mounted backup destination</source>
            <translation>选择已挂载的备份目标</translation>
        </message>
        <message>
            <source>Invalid machine identity</source>
            <translation>机器标识无效</translation>
        </message>
        <message>
            <source>Enter a machine name using letters, digits, dots, underscores or hyphens (maximum 64 characters).</source>
            <translation>机器名称只能使用字母、数字、点、下划线或连字符（最多 64 个字符）。</translation>
        </message>
        <message>
            <source>Invalid Btrfs source</source>
            <translation>Btrfs 来源无效</translation>
        </message>
        <message>
            <source>Choose an accessible Snapper snapshot path and an initialized CAS repository.</source>
            <translation>请选择可访问的 Snapper 快照路径和已经初始化的 CAS 仓库。</translation>
        </message>
        <message>
            <source>Experimental CAS send</source>
            <translation>实验性 CAS 发送</translation>
        </message>
        <message>
            <source>Send the selected readonly Snapper snapshot using the experimental content-addressed engine? This creates a distinct CAS archive format; it does not overwrite previous Harbor archives.</source>
            <translation>是否使用实验性的内容寻址引擎发送所选的只读 Snapper 快照？这将创建一种单独的 CAS 归档格式，不会覆盖之前的 Harbor 归档。</translation>
        </message>
        <message>
            <source>Invalid selection</source>
            <translation>选择无效</translation>
        </message>
        <message>
            <source>Select a valid Snapper snapshot and an absolute destination.</source>
            <translation>请选择有效的 Snapper 快照和绝对路径目标目录。</translation>
        </message>
        <message>
            <source>Start backup</source>
            <translation>开始备份</translation>
        </message>
        <message>
            <source>Send snapshot %1 to %2?</source>
            <translation>将快照 %1 发送到 %2？</translation>
        </message>
        <message>
            <source>Invalid destination</source>
            <translation>目标目录无效</translation>
        </message>
        <message>
            <source>Select an existing absolute CAS directory.</source>
            <translation>请选择已存在的 CAS 绝对路径目录。</translation>
        </message>
        <message>
            <source>Initialize CAS</source>
            <translation>初始化 CAS</translation>
        </message>
        <message>
            <source>Initialize or open the dedicated CAS repository in this destination? Existing legacy archives are not modified.</source>
            <translation>是否在该目标位置初始化或打开专用 CAS 仓库？现有的旧格式归档不会被修改。</translation>
        </message>
        <message>
            <source>Invalid legacy repository</source>
            <translation>旧版仓库无效</translation>
        </message>
        <message>
            <source>Select an absolute checkpoint-v2 repository before listing machine sets.</source>
            <translation>列出机器备份集合之前，请选择检查点 v2 仓库的绝对路径。</translation>
        </message>
        <message>
            <source>Machine repository changed</source>
            <translation>机器仓库已改变</translation>
        </message>
        <message>
            <source>The destination changed since listing machine sets. Refresh the catalog first.</source>
            <translation>列出机器备份集合后，目标位置发生了变化。请先刷新目录。</translation>
        </message>
        <message>
            <source>Invalid machine restore preview</source>
            <translation>机器恢复预览无效</translation>
        </message>
        <message>
            <source>Select an existing machine backup set and a new empty Btrfs staging directory. This operation never changes the running system.</source>
            <translation>请选择已有的机器备份集合以及一个新的空 Btrfs 暂存目录。此操作不会更改正在运行的系统。</translation>
        </message>
        <message>
            <source>No resumable transfer</source>
            <translation>没有可恢复的传输</translation>
        </message>
        <message>
            <source>Open Interrupted transfers, then select a valid partial checkpoint.</source>
            <translation>打开“中断的传输”，然后选择有效的部分检查点。</translation>
        </message>
        <message>
            <source>Resume checkpoint</source>
            <translation>恢复检查点</translation>
        </message>
        <message>
            <source>Resume archive %1 using its existing verified checkpoints? An active transfer holds a lock and cannot be opened twice.</source>
            <translation>是否使用已验证的检查点恢复归档 %1？正在运行的传输会持有锁，不能重复打开。</translation>
        </message>
        <message>
            <source>Invalid schedule</source>
            <translation>定时任务无效</translation>
        </message>
        <message>
            <source>Choose a valid Snapper config, destination and frequency.</source>
            <translation>请选择有效的 Snapper 配置、目标位置和频率。</translation>
        </message>
        <message>
            <source>Install systemd timer</source>
            <translation>安装 systemd 定时器</translation>
        </message>
        <message>
            <source>Install and enable an automatic %1 transfer for %2? It will use the selected engine. Snapper snapshots will not be created or deleted.</source>
            <translation>是否安装并启用将 %2 按 %1 频率自动传输的任务？它将使用所选引擎，不会创建或删除 Snapper 快照。</translation>
        </message>
        <message>
            <source>Choose an existing Snapper configuration and destination.</source>
            <translation>请选择已有的 Snapper 配置和目标位置。</translation>
        </message>
        <message>
            <source>Stop and remove the automatic timer for this configuration and destination? No snapshot or backup files will be deleted.</source>
            <translation>是否停止并删除此配置和目标位置的自动定时器？不会删除任何快照或备份文件。</translation>
        </message>
        <message>
            <source>No CAS archive selected</source>
            <translation>未选择 CAS 归档</translation>
        </message>
        <message>
            <source>Select a committed CAS archive.</source>
            <translation>请选择已提交的 CAS 归档。</translation>
        </message>
        <message>
            <source>Archive belongs to another machine</source>
            <translation>归档属于另一台机器</translation>
        </message>
        <message>
            <source>Select the correct machine identity and refresh the repository list before pruning.</source>
            <translation>在清理归档前，请选择正确的机器标识并刷新仓库列表。</translation>
        </message>
        <message>
            <source>Invalid CAS destination</source>
            <translation>CAS 目标位置无效</translation>
        </message>
        <message>
            <source>Choose a CAS repository first.</source>
            <translation>请先选择 CAS 仓库。</translation>
        </message>
        <message>
            <source>Missing archive</source>
            <translation>归档缺失</translation>
        </message>
        <message>
            <source>Select a completed CAS archive.</source>
            <translation>请选择已完成的 CAS 归档。</translation>
        </message>
        <message>
            <source>Select a valid archive and destination.</source>
            <translation>请选择有效的归档和目标位置。</translation>
        </message>
        <message>
            <source>Invalid recovery</source>
            <translation>恢复参数无效</translation>
        </message>
        <message>
            <source>Choose an archive and an empty absolute Btrfs staging directory.</source>
            <translation>请选择归档和空的 Btrfs 绝对路径暂存目录。</translation>
        </message>
        <message>
            <source>Select an archive and an absolute non-root staging directory.</source>
            <translation>请选择归档和不属于根目录的绝对路径暂存目录。</translation>
        </message>
        <message>
            <source>Backend diagnostic line exceeded 64 KiB; truncating.</source>
            <translation>后端诊断行超过 64 KiB；已截断。</translation>
        </message>
        <message>
            <source>Source stream read: %1 GiB — average %2 MiB/s (raw; total unknown)</source>
            <translation>已读取源数据流：%1 GiB — 平均 %2 MiB/秒（原始数据量；总量未知）</translation>
        </message>
        <message>
            <source>Stopping current operation...</source>
            <translation>正在停止当前操作……</translation>
        </message>
        <message>
            <source>Harbor CLI not found or failed to start: %1</source>
            <translation>未找到 Harbor 命令行程序或启动失败：%1</translation>
        </message>
        <message>
            <source>Cannot start Harbor CLI</source>
            <translation>无法启动 Harbor 命令行程序</translation>
        </message>
        <message>
            <source>None — full send</source>
            <translation>无 — 完整发送</translation>
        </message>
        <message>
            <source>Busy</source>
            <translation>忙碌</translation>
        </message>
        <message>
            <source>An operation is already running.</source>
            <translation>已有操作正在运行。</translation>
        </message>
        <message>
            <source>Backend not trusted</source>
            <translation>后端不可信</translation>
        </message>
        <message>
            <source>The backup backend must be installed as a root-owned executable in /usr/bin or /usr/local/bin, with no group/world-write permission, and with trusted parent directories. Refusing to run an executable from the user PATH: %1</source>
            <translation>备份后端必须以 root 所有、不可被组或其他用户写入的可执行文件形式安装在 /usr/bin 或 /usr/local/bin 中，且其父目录必须可信。拒绝从用户 PATH 执行程序：%1</translation>
        </message>
        <message>
            <source>Running: %1</source>
            <translation>运行中：%1</translation>
        </message>
        <message>
            <source>Choose an absolute CAS directory.</source>
            <translation>请选择 CAS 目录的绝对路径。</translation>
        </message>
        <message>
            <source>Choose an absolute backup directory.</source>
            <translation>请选择备份目录的绝对路径。</translation>
        </message>
        <message>
            <source>Operation cancelled; incomplete transfer must be resumed or retried.</source>
            <translation>操作已取消；未完成的传输必须恢复或重试。</translation>
        </message>
        <message>
            <source>Operation finished: %1</source>
            <translation>操作完成：%1</translation>
        </message>
        <message>
            <source>Operation failed: %1 (exit %2)</source>
            <translation>操作失败：%1（退出码 %2）</translation>
        </message>
        <message>
            <source>Invalid filesystem inventory response.</source>
            <translation>文件系统清单响应无效。</translation>
        </message>
        <message>
            <source>Unsupported machine inventory schema or invalid counts.</source>
            <translation>机器清单架构不受支持或计数无效。</translation>
        </message>
        <message>
            <source>Invalid machine inventory warning; refusing result.</source>
            <translation>机器清单警告无效；拒绝此结果。</translation>
        </message>
        <message>
            <source>Detected %1 included Btrfs volumes.
Coverage inventory: %2.
Bootable bare-metal recovery: NOT CERTIFIED.
%3</source>
            <translation>检测到 %1 个纳入备份的 Btrfs 卷。
覆盖清单：%2。
可启动的裸机恢复：尚未认证。
%3</translation>
        </message>
        <message>
            <source>complete for supported mount types</source>
            <translation>对受支持的挂载类型覆盖完整</translation>
        </message>
        <message>
            <source>incomplete — backup must be refused</source>
            <translation>覆盖不完整 — 必须拒绝备份</translation>
        </message>
        <message>
            <source>Machine coverage audit</source>
            <translation>机器备份覆盖范围审核</translation>
        </message>
        <message>
            <source>Missing machine coverage</source>
            <translation>机器备份覆盖范围缺失</translation>
        </message>
        <message>
            <source>Machine-set catalog destination changed while reading; refusing stale catalog.</source>
            <translation>读取机器备份目录期间目标位置发生变化；拒绝使用过期目录。</translation>
        </message>
        <message>
            <source>Machine-set catalog rejected: %1</source>
            <translation>机器备份目录被拒绝：%1</translation>
        </message>
        <message>
            <source>%1 — %2 Btrfs volumes, %3 boot-file sets — %4 — NOT bootable</source>
            <translation>%1 — %2 个 Btrfs 卷，%3 组启动文件 — %4 — 不可启动</translation>
        </message>
        <message>
            <source>QA staging preview available</source>
            <translation>可进行质量测试暂存预览</translation>
        </message>
        <message>
            <source>INCOMPLETE: %1</source>
            <translation>未完成：%1</translation>
        </message>
        <message>
            <source>Incomplete machine backup set: preview restore unavailable.</source>
            <translation>机器备份集合不完整：无法预览恢复。</translation>
        </message>
        <message>
            <source>Machine-set preview destination, staging or selection changed; refusing stale result.</source>
            <translation>机器备份预览所用的目标位置、暂存目录或选择已改变；拒绝过期结果。</translation>
        </message>
        <message>
            <source>Machine restore preview rejected: %1</source>
            <translation>机器恢复预览被拒绝：%1</translation>
        </message>
        <message>
            <source>Validated staged recovery preview</source>
            <translation>已验证的分阶段恢复预览</translation>
        </message>
        <message>
            <source>Backend preflight validated: %1 separate Btrfs volumes, %2 boot-file archives.
Original mount points (first 12): %3
Nothing was restored. A bootable computer is NOT promised. Bare-metal recovery still requires validated ReaR/EFI rescue.</source>
            <translation>后端预检通过：%1 个独立 Btrfs 卷、%2 组启动文件归档。
原始挂载点（前 12 个）：%3
未恢复任何数据。不保证计算机可以启动。裸机恢复仍需经过验证的 ReaR/EFI 救援。</translation>
        </message>
        <message>
            <source>Prune preview invalid; refusing deletion.</source>
            <translation>清理预览无效；拒绝删除。</translation>
        </message>
        <message>
            <source>Prune plan mismatch or destination changed; refusing deletion.</source>
            <translation>清理计划不匹配或目标位置已改变；拒绝删除。</translation>
        </message>
        <message>
            <source>Permanently delete the selected CAS archive %1 and reclaim unreferenced chunks?</source>
            <translation>是否永久删除所选 CAS 归档 %1 并回收不再被引用的数据块？</translation>
        </message>
        <message>
            <source>Reclaim orphan CAS chunks from aborted transfers? No committed archive will be removed.</source>
            <translation>是否回收中断传输留下的孤立 CAS 数据块？不会删除任何已提交的归档。</translation>
        </message>
        <message>
            <source>Confirm destructive CAS cleanup</source>
            <translation>确认破坏性 CAS 清理</translation>
        </message>
        <message>
            <source>
Estimated reclaimable compressed data: %1 MiB.
This cannot be undone. The plan will be checked again under repository lock.</source>
            <translation>
预计可回收的压缩数据：%1 MiB。
此操作无法撤销。执行前将再次在仓库锁保护下验证计划。</translation>
        </message>
        <message>
            <source>CAS pruning finished; refreshing archive inventory.</source>
            <translation>CAS 清理已完成；正在刷新归档清单。</translation>
        </message>
        <message>
            <source>Archive inventory is not valid JSON; no selection was changed.</source>
            <translation>归档清单不是有效的 JSON；没有更改任何选择。</translation>
        </message>
        <message>
            <source>Checkpoint inventory is invalid; no selection was changed.</source>
            <translation>检查点清单无效；没有更改任何选择。</translation>
        </message>
        <message>
            <source>Confirm staged Btrfs receive</source>
            <translation>确认分阶段 Btrfs 接收</translation>
        </message>
        <message>
            <source>CAS archive chain verified. Receive every required snapshot into the selected empty Btrfs staging directory? This will not activate a system rollback.</source>
            <translation>CAS 归档链已验证。是否将所有必需的快照接收到所选的空 Btrfs 暂存目录？此操作不会激活系统回滚。</translation>
        </message>
        <message>
            <source>Confirm recovery</source>
            <translation>确认恢复</translation>
        </message>
        <message>
            <source>Dry-run successful. Restore the selected snapshot into the staging directory? Existing system subvolumes will not be replaced.</source>
            <translation>试运行成功。是否将所选快照恢复到暂存目录？不会替换现有的系统子卷。</translation>
        </message>
            <message>
            <source>Backup context changed; refresh archives before pruning.</source>
            <translation>备份上下文已更改；清理前请刷新归档列表。</translation>
        </message>
        <message>
            <source>Backup context changed; refusing stale archive catalog.</source>
            <translation>备份上下文已更改；拒绝使用过期的归档列表。</translation>
        </message>
        <message>
            <source>Backup or recovery destination changed; refusing stale restore preview.</source>
            <translation>备份或恢复目标已更改；拒绝使用过期的恢复预览。</translation>
        </message>
    </context>
    <context>
        <name>HarborLanguage</name>
        <message>
            <source>Interface language</source>
            <translation>界面语言</translation>
        </message>
        <message>
            <source>Choose English, French or Simplified Chinese. Reopen Harbor to apply.</source>
            <translation>选择英语、法语或简体中文。重新打开 Harbor 以应用语言。</translation>
        </message>
        <message>
            <source>Language saved</source>
            <translation>语言设置已保存</translation>
        </message>
        <message>
            <source>Close and reopen Harbor to apply the selected language to every screen.</source>
            <translation>关闭并重新打开 Harbor，以在所有界面中应用所选语言。</translation>
        </message>
        <message>
            <source>Language setting failed</source>
            <translation>语言设置失败</translation>
        </message>
        <message>
            <source>The language preference could not be saved.</source>
            <translation>无法保存语言偏好设置。</translation>
        </message>
    </context>
</TS>
