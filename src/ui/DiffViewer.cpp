#include "ui/DiffViewer.h"
#include "util/System.h"

#include <QDialog>
#include <QDir>
#include <QFileInfo>
#include <QRegularExpression>
#include <QMessageBox>

DiffViewer::DiffViewer(Snapper *snapper, const QString &rootPath, const QString &filePath, const QString &uuid, QWidget *parent)
    : QDialog(parent), m_ui(new Ui::DiffViewer), m_snapper(snapper), m_uuid(uuid)
{

    m_ui->setupUi(this);

    this->setWindowTitle(tr("Diff Viewer"));

    m_twSnapshot = m_ui->tableWidget_snapshotList;

    // We will need the target path for both diffs and restores
    m_targetPath = m_snapper->findTargetPath(rootPath, filePath, uuid);

    // We need to find all the snapshots with the file in them and populate the UI
    LoadSnapshots(rootPath, filePath);
}

DiffViewer::~DiffViewer() { delete m_ui; }

void DiffViewer::on_pushButton_restore_clicked()
{
    if (QMessageBox::question(0, tr("Confirm"), tr("Are you sure you want to restore this the file over the current file?")) !=
        QMessageBox::Yes) {
        return;
    }

    // Restore the file
    const int row = m_twSnapshot->currentRow();
    const auto *entry = row >= 0 ? m_twSnapshot->item(row, DiffColumn::filePath) : nullptr;
    const QString filePath = entry != nullptr ? entry->text() : QString();

    if (m_targetPath.isEmpty() || filePath.isEmpty() || !m_snapper->restoreFile(filePath, m_targetPath)) {
        QMessageBox::warning(this, tr("Restore Failed"), tr("The file failed to restore"));
        return;
    }

    QMessageBox::information(this, tr("Restore File"), tr("The file was successfully restored"));
}

QStringList DiffViewer::snapshotFileCandidates(const QString &rootPath, const QString &filePath)
{
    const QString root = QDir(rootPath).canonicalPath();
    const QString selected = QFileInfo(filePath).canonicalFilePath();
    const auto match = QRegularExpression(QStringLiteral("^(.+)/([0-9]+)/snapshot$")).match(root);
    if (!match.hasMatch() || selected.isEmpty() ||
        !selected.startsWith(root + QLatin1Char('/'))) return {};

    const QString stem = QDir(match.captured(1)).canonicalPath();
    if (stem.isEmpty()) return {};
    const QString relative = QDir(root).relativeFilePath(selected);
    if (relative.isEmpty() || relative == QLatin1String(".") ||
        relative == QLatin1String("..") || relative.startsWith(QLatin1String("../")) ||
        QDir::isAbsolutePath(relative)) return {};

    QStringList matches;
    const QDir snapshotHomes(stem);
    for (const auto &number : snapshotHomes.entryList(QDir::Dirs | QDir::NoDotAndDotDot)) {
        bool numeric = false;
        const uint id = number.toUInt(&numeric);
        if (!numeric || id == 0 || QString::number(id) != number) continue;
        const QString snapshotRoot = QDir(stem).filePath(number + QLatin1String("/snapshot"));
        const QString actualRoot = QDir(snapshotRoot).canonicalPath();
        if (actualRoot.isEmpty() || !actualRoot.startsWith(stem + QLatin1Char('/')))
            continue;
        const QString candidate = QDir(snapshotRoot).filePath(relative);
        const QFileInfo info(candidate);
        if (!info.isFile() || !info.canonicalFilePath().startsWith(actualRoot + QLatin1Char('/')))
            continue;
        matches.append(candidate);
    }
    return matches;
}

void DiffViewer::LoadSnapshots(const QString &rootPath, const QString &filePath)
{
    const QStringList resultList = snapshotFileCandidates(rootPath, filePath);
    const QString canonicalRoot = QDir(rootPath).canonicalPath();
    const auto match = QRegularExpression(QStringLiteral("^(.+)/([0-9]+)/snapshot$"))
                           .match(canonicalRoot);
    const QDir stemPath(match.hasMatch() ? match.captured(1) : QString());

    m_twSnapshot->clear();
    m_twSnapshot->setColumnCount(4);
    m_twSnapshot->setHorizontalHeaderItem(DiffColumn::num, new QTableWidgetItem(tr("Num", "The number associated with a snapshot")));
    m_twSnapshot->setHorizontalHeaderItem(DiffColumn::dateTime, new QTableWidgetItem(tr("Date/Time")));
    m_twSnapshot->setHorizontalHeaderItem(DiffColumn::rootPath, new QTableWidgetItem(tr("Root Path")));
    m_twSnapshot->setHorizontalHeaderItem(DiffColumn::filePath, new QTableWidgetItem(tr("File Path")));
    m_twSnapshot->setColumnHidden(DiffColumn::rootPath, true);
    m_twSnapshot->setColumnHidden(DiffColumn::filePath, true);
    m_twSnapshot->setRowCount(static_cast<int>(resultList.size()));

    const QLocale locale = QLocale::system();
    int row = 0;
    for (const QString &result : resultList) {
        const QString relative = stemPath.relativeFilePath(result);
        const QString snapshotNum = relative.section(QLatin1Char('/'), 0, 0);
        const QString thisRootPath = stemPath.filePath(snapshotNum + QLatin1String("/snapshot"));
        const QString metaFileName = stemPath.filePath(snapshotNum + QLatin1String("/info.xml"));
        const QString date = locale.toString(Snapper::readSnapperMeta(metaFileName).time, QLocale::ShortFormat);
        auto *number = new QTableWidgetItem();
        number->setData(Qt::DisplayRole, snapshotNum.toUInt());
        m_twSnapshot->setItem(row, DiffColumn::num, number);
        m_twSnapshot->setItem(row, DiffColumn::dateTime, new QTableWidgetItem(date));
        m_twSnapshot->setItem(row, DiffColumn::rootPath, new QTableWidgetItem(thisRootPath));
        m_twSnapshot->setItem(row, DiffColumn::filePath, new QTableWidgetItem(result));
        if (result == filePath) m_twSnapshot->selectRow(row);
        ++row;
    }
    m_twSnapshot->resizeColumnsToContents();
    m_twSnapshot->sortItems(DiffColumn::num, Qt::DescendingOrder);
}

void DiffViewer::on_tableWidget_snapshotList_itemSelectionChanged()
{
    const int row = m_twSnapshot->currentRow();
    const auto *entry = row >= 0 ? m_twSnapshot->item(row, DiffColumn::filePath) : nullptr;
    if (entry == nullptr || m_targetPath.isEmpty()) return;
    const QString filePath = entry->text();
    const QStringList diffOutput = System::runCmd("diff", {"-u", m_targetPath, filePath}, false).output.split("\n");

    if (diffOutput.isEmpty() || diffOutput.at(0).isEmpty()) {
        m_ui->textEdit_diff->setText(tr("There are no differences between the selected files"));
        return;
    }

    // Get a copy of the palette before we start changing colors
    QPalette defaultPalette = m_ui->textEdit_diff->palette();

    // Show the diff
    m_ui->textEdit_diff->clear();
    for (const QString &line : diffOutput) {
        // Colorize the output for lines added or removed
        if (line.startsWith("+")) {
            m_ui->textEdit_diff->setTextColor(Qt::darkGreen);
        } else if (line.startsWith("-")) {
            m_ui->textEdit_diff->setTextColor(Qt::red);
        }

        m_ui->textEdit_diff->append(line);
        m_ui->textEdit_diff->setTextColor(defaultPalette.text().color());
    }
}
