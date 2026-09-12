param([Parameter(Mandatory=$true)][int]$PanelPid,
      [Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;using System.Text;using System.Collections.Generic;using System.Runtime.InteropServices;
public class PanelRead {
 [StructLayout(LayoutKind.Sequential)] public struct Rect {public int L,T,R,B;}
 public delegate bool EnumProc(IntPtr h,IntPtr p);
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int cmd);
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h,out Rect r);
 [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h,IntPtr dc,uint flags);
 [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr h,EnumProc fn,IntPtr p);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr h,StringBuilder b,int n);
 public static string[] Children(IntPtr parent){var list=new List<string>();EnumChildWindows(parent,(h,p)=>{var c=new StringBuilder(256);Rect r;GetClassName(h,c,256);GetWindowRect(h,out r);list.Add(h+" class="+c+" rect="+r.L+","+r.T+","+r.R+","+r.B);return true;},IntPtr.Zero);return list.ToArray();}
}
'@
$panelProcess=Get-Process -Id $PanelPid
if($panelProcess.MainWindowTitle -ne 'Chimera membrane demo'){throw 'wrong window'}
if(Test-Path -LiteralPath $OutputPath){throw 'existing capture'}
[void][PanelRead]::ShowWindow($panelProcess.MainWindowHandle,9)
Start-Sleep -Milliseconds 300
$rect=New-Object PanelRead+Rect
if(-not [PanelRead]::GetWindowRect($panelProcess.MainWindowHandle,[ref]$rect)){throw 'rectangle failed'}
$bitmap=New-Object System.Drawing.Bitmap(($rect.R-$rect.L),($rect.B-$rect.T))
$graphics=[System.Drawing.Graphics]::FromImage($bitmap)
$dc=$graphics.GetHdc()
try {
    if(-not [PanelRead]::PrintWindow($panelProcess.MainWindowHandle,$dc,0)){throw 'capture failed'}
} finally {$graphics.ReleaseHdc($dc)}
try {$bitmap.Save($OutputPath,[System.Drawing.Imaging.ImageFormat]::Png)}
finally {$graphics.Dispose();$bitmap.Dispose()}
[PanelRead]::Children($panelProcess.MainWindowHandle)
