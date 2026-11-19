param(
    [Parameter(Mandatory = $true)][string]$Docx,
    [Parameter(Mandatory = $true)][string]$Pdf
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms | Out-Null
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($Docx, $false, $true)
    $pages = $doc.ComputeStatistics(2)  # wdStatisticPages
    $doc.ExportAsFixedFormat($Pdf, 17, $false, 0, 1, 0, 0)  # wdExportFormatPDF
    $doc.Close($false)
    Write-Output "pages=$pages"
    Write-Output "pdf=$Pdf"
}
finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
