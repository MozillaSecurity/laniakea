#
# domino-launch.ps1
#
param (
  $vmAdminUsername,
  $vmAdminPassword,
  $aws_key_id,
  $aws_secret
)
 
$password =  ConvertTo-SecureString $vmAdminPassword -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential("$env:USERDOMAIN\$vmAdminUsername", $password)

$Profile = Get-NetConnectionProfile -InterfaceAlias Ethernet
$Profile.NetworkCategory = "Private"
Set-NetConnectionProfile -InputObject $Profile

Enable-PSRemoting -force
 
Invoke-Command -Credential $credential -ComputerName $env:COMPUTERNAME -ArgumentList $aws_key_id, $aws_secret -ScriptBlock {
    param 
    (
        $aws_key_id,
        $aws_secret
    )
    
    Set-ExecutionPolicy Bypass -Scope Process -Force; iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
    choco feature enable -n allowGlobalConfirmation
    choco install openssh
    choco install git
    choco install python2
    choco install nodejs

    # Create support files
    New-Item -path $env:userprofile\.aws\credentials -force
    Add-Content -path $env:userprofile\.aws\credentials -Value "[default]"
    Add-Content -path $env:userprofile\.aws\credentials -Value "aws_secret_key_id = $aws_key_id"
    Add-Content -path $env:userprofile\.aws\credentials -Value "aws_secret_access_key = $aws_secret"
    
    New-Item -path $env:userprofile\requirements.txt -ItemType file
    Add-Content -path $env:userprofile\requirements.txt -value "git+https://github.com/MozillaSecurity/fuzzfetch.git"
    Add-Content -path $env:userprofile\requirements.txt -value "git+https://github.com/MozillaSecurity/ffpuppet.git"
    Add-Content -path $env:userprofile\requirements.txt -value "git+ssh://git@sapphire/MozillaSecurity/sapphire.git"
    Add-Content -path $env:userprofile\requirements.txt -value "git+https://github.com/MozillaSecurity/avalanche.git"
    Add-Content -path $env:userprofile\requirements.txt -value "git+https://github.com/MozillaSecurity/FuzzManager.git"

    if (!(Test-Path "$env:userprofile\.ssh\config"))
    {
        New-Item -path $env:userprofile\.ssh\config -type "file" -force
    }
    else
    {
        Add-Content -path $env:userprofile\.ssh\config -value "`r`n"
    }
    Add-Content -path $env:userprofile\.ssh\config -value "Host grizzly"
    Add-Content -path $env:userprofile\.ssh\config -value "HostName github.com"
    Add-Content -path $env:userprofile\.ssh\config -value "IdentitiesOnly yes"
    Add-Content -path $env:userprofile\.ssh\config -value "IdentityFile $env:userprofile\.ssh\id_ecdsa.grizzly"
    Add-Content -path $env:userprofile\.ssh\config -value "StrictHostKeyChecking no"
    Add-Content -path $env:userprofile\.ssh\config -value "`r`n"
    Add-Content -path $env:userprofile\.ssh\config -value "Host grizzly-private"
    Add-Content -path $env:userprofile\.ssh\config -value "HostName github.com"
    Add-Content -path $env:userprofile\.ssh\config -value "IdentitiesOnly yes"
    Add-Content -path $env:userprofile\.ssh\config -value "IdentityFile $env:userprofile\.ssh\id_ecdsa.grizzly-private"
    Add-Content -path $env:userprofile\.ssh\config -value "StrictHostKeyChecking no"
    Add-Content -path $env:userprofile\.ssh\config -value "`r`n"
    Add-Content -path $env:userprofile\.ssh\config -value "Host sapphire"
    Add-Content -path $env:userprofile\.ssh\config -value "HostName github.com"
    Add-Content -path $env:userprofile\.ssh\config -value "IdentitiesOnly yes"
    Add-Content -path $env:userprofile\.ssh\config -value "IdentityFile $env:userprofile\.ssh\id_ecdsa.sapphire"
    Add-Content -path $env:userprofile\.ssh\config -value "StrictHostKeyChecking no"
    Add-Content -path $env:userprofile\.ssh\config -value "`r`n"
    Add-Content -path $env:userprofile\.ssh\config -value "Host DOMfuzz2"
    Add-Content -path $env:userprofile\.ssh\config -value "HostName github.com"
    Add-Content -path $env:userprofile\.ssh\config -value "IdentitiesOnly yes"
    Add-Content -path $env:userprofile\.ssh\config -value "IdentityFile $env:userprofile\.ssh\id_ecdsa.domino"
    Add-Content -path $env:userprofile\.ssh\config -value "StrictHostKeyChecking no"
    Add-Content -path $env:userprofile\.ssh\config -value "`r`n"
    Add-Content -path $env:userprofile\.ssh\config -value "Host fuzzidl"
    Add-Content -path $env:userprofile\.ssh\config -value "HostName github.com"
    Add-Content -path $env:userprofile\.ssh\config -value "IdentitiesOnly yes"
    Add-Content -path $env:userprofile\.ssh\config -value "IdentityFile $env:userprofile\.ssh\id_ecdsa.fuzzidl"
    Add-Content -path $env:userprofile\.ssh\config -value "StrictHostKeyChecking no"
    Add-Content -path $env:userprofile\.ssh\config -value "`r`n"
}

Invoke-Command -Credential $credential -ComputerName $env:COMPUTERNAME -ArgumentList $aws_key_id, $aws_secret -ScriptBlock {
    param 
    (
        $aws_key_id,
        $aws_secret
    )
    
    python -m pip install --upgrade pip
    
    pip install boto
    pip install credstash
    
    refreshenv

    $env:AWS_ACCESS_KEY_ID=$aws_key_id
    $env:AWS_SECRET_ACCESS_KEY=$aws_secret
    
    credstash -r us-east-1 get deploy-grizzly.pem | Out-File $env:userprofile\.ssh\id_ecdsa.grizzly -Encoding ASCII
    credstash -r us-east-1 get deploy-grizzly-private.pem | Out-File $env:userprofile\.ssh\id_ecdsa.grizzly-private -Encoding ASCII
    credstash -r us-east-1 get deploy-sapphire.pem | Out-File $env:userprofile\.ssh\id_ecdsa.sapphire -Encoding ASCII
    credstash -r us-east-1 get deploy-domino.pem | Out-File $env:userprofile\.ssh\id_ecdsa.domino -Encoding ASCII
    credstash -r us-east-1 get deploy-fuzzidl.pem | Out-File $env:userprofile\.ssh\id_ecdsa.fuzzidl -Encoding ASCII
    credstash -r us-east-1 get fuzzmanagerconf | Out-File $env:userprofile\.fuzzmanagerconf -Encoding ASCII

    Add-Content -path $env:userprofile\.fuzzmanagerconf -Value "sigdir = $env:userprofile\signatures"
    Add-Content -path $env:userprofile\.fuzzmanagerconf -Value "tool = domino-windows"
}

Invoke-Command -Credential $credential -ComputerName $env:COMPUTERNAME -ScriptBlock {
    git clone -v --depth 1 git@DOMfuzz2:pyoor/DOMfuzz2.git domino
    Set-Location -Path $env:userprofile\domino
    npm install -ddd
    npm run build
}
Invoke-Command -Credential $credential -ComputerName $env:COMPUTERNAME -ScriptBlock {
    pip install -U -r $env:userprofile\requirements.txt
    
    git clone -v --branch legacy --depth 1 https://github.com/MozillaSecurity/fuzzpriv.git
    git clone -v --depth 1 git@grizzly:MozillaSecurity/grizzly.git
    git clone -v --depth 1 git@grizzly-private:MozillaSecurity/grizzly-private.git grizzly-private
    xcopy grizzly-private /O /X /E /H /K /f /Y grizzly

    New-Item -ItemType Directory $env:userprofile\signatures
    python -m Collector.Collector --refresh

    fuzzfetch -n firefox --asan

    Set-Location -Path $env:userprofile\documents\grizzly
  
    $env:DOMINO_ROOT="$env:userprofile\documents\domino"
    $env:ITERS=100

     while($true)
     {
        python grizzly.py ..\firefox\firefox.exe $env:userprofile\documents\domino\reftests\ domino --accepted-extensions html xhtml --cache 5 -m 7000 -p prefs\prefs-default-e10s.js --relaunch 50 --timeout 120 --ignore log-limit memory timeout --extension=..\fuzzpriv --fuzzmanager
        if($error){
            Start-sleep 60
        }
    }
}
