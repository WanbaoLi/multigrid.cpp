# Historical comparison checkpoint, now closed

Superseded by [v3 final report](../comparison-20261105-v3/REPORT.md).

Latest user scope: compare PyQCU and our solver on login and compute, smear ON
once, both iterative stopping tolerance1e-8. Exclude one-time preprocess/smear/
Clover/setup/IO from pure solve. User clarified tolerance is each solver's own
relative residual, not cross-library solution error. Do NOT ask again. No agents.

New local cwd C:/Users/lwb/Documents/ChatGPT/multigrid.cpp was empty.git. Fetched
old delivery repo locally and checked out codex/fair-pyqcu-comparison-20261105
at9b99af2. Author/email inherited correct. No origin set yet. All new work in
comparison-20261105 andcomparison-20261105-v2, numerical code unchanged.
Old delivery stays untouched at C:/Users/lwb/Documents/Codex/2026-11-02/simd-lqcd-2.

RootR=/home/share/nsls_lwb/.cache/fair-solve-20261105-v2
PY=/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python
Login hostname login04,128 physical cores. Compute Donau job2039150 oncn19486,
exclusive592cores/480000MB, start07:41:09UTCNov5,4h harddeadline11:41:09UTC.
Worker queueR/compute-queue, lifetime14000,idle1800, workerpid2014852.
Login queueR/login-queue, lifetime14400,idle1800, no exclusive node.
Original1e-10 experimentRendingv1 superseded: all queuesSTOP, alltasksclosed
cleanupempty; loginours pilot TERM by human-scopechange, retainedfailed. Job
2038996cn19480 stoppedcleanly; don'tcountold1e-10asnewresults.

Commoninputprepared fromold canonicalDPpoststoutfixture
/home/share/nsls_lwb/.cache/mg-20261102/propagator/gauge_rank00000..15.npy.
CanonicalSHA126d658999367b0ece3801c61cd143542d7db0dddc37ab60e6e668e18faa6834.
R/input/gauge-untwisted.npy forours (internal antiperiodic). PyQCU sameDPbytes
transposed3,3,4,x,y,z,t toHDF5data, onlylastt temporal link negatedonce:
R/input/gauge-pyqcu-ap-c128.h5. m-.277,csw1.160920226,originunit12sources.
PyQCU c128BiCGStab levels1/restart0, NOTmultigrid. Source8a846bf knownDPsupport.
OurmixedprecisionMG usesoriginalsource297/exactnumerics5fe052.

Pilot1e-8 passed:
- loginours full12pilot nativeAPI77.644577s,setupoutside; all12true<=1e-8.
- loginPyQCU COLUMN0only161.332760s, residual5.310947e-10, norestarter.
- computePyQCU COLUMN0only89.951356s, residual5.621698e-10.
- Pilotcross-librarylogincolumn0 relerror6.58173998e-8 (limit1e-6 pass).
Old1e-10compute crossrel1.129386e-9 alsoestablishedsameoperator; neverrankold.
CrosscheckusesPyQCUx/3.723 to matchmassnormalization; convertstzyxsc layouts
andgathersactualprocessgrid. All12residuals gates, crosscol0onlydiagnostic.

Actualworkers useexisting source297/tools/optimization/worker.py withsafe
taggedcleanup. Python supervisorsR/sequence.py login/compute launchednohup,
logsR/login-sequence.log+compute-sequence.log. They sequentiallyqueueandwait,
neveroverlapnumericalworkononehost. Existingfailedtasksblock,notautooverwrite.

CURRENT~07:58:43UTC:
- computeours-128-full closedPASSED494s cleanupempty. Sourceoriginald8b2e052lib.
  warmnativeAPI69.976921458; steady69.762635567/69.780959107/69.770030979s.
  pureinternal narrower69.206721127/69.224800421/69.214145494.
  PythonfullAPI70.180830387/70.203164674/70.187921999.
- computepyqcu-128-full juststarted~07:56:50;firstcolumnfinished~90s.
- loginours-128-full stillrunning~485selapsed, steady1nativeAPI75.494348307,
  steady2 83.359460207; finalsamplepending. Sharedload,keepallsamples.
- loginpyqcu-128-full notstartedyet, supervisorqueuesafterourscloses.

Supervisorcompute schedule: ours128(alreadyclosed),pyqcu128(current),ours592,
pyqcu592, thencrosscheck128/592full, writescompute-sequence-complete.json.
Supervisorlogin: waitbothpilots,crosscheckpassed,ours128current,pyqcu128,
crosscheckfull,writeslogin-sequence-complete.json.

For128fair samephysicalcores4MPIx32. Oursgrid1,1,1,4; PyQCUgrid1,4,1,1.
Defaultmemoryoff both. Whole-nodebest: ours16ranks37setup/32solve=512active,
HBWrequire;PyQCU16x37=592,grid1,4,4,1,defaultmemory. Reportdifferences.
R/run_ours_full.sh usesR/ours_full.py (4calls1warm+3steady), actual--setup-threads.
R/run_pyqcu_full.sh usesR/pyqcu_entry_full.py ->R/pyqcu_repeated_full.py.
Userdoesn'tneedoverlyrigorous repetition; afterpilotcosts, changedPyQCUfull
driverBEFOREanyfullPyQCUrun from4to2complete12calls: first+onesteady. Tolduser.
Prepared4-calloriginalretainedR/pyqcu_repeated_four_prepared_not_run.py.
Allfirst/steadyvaluesretained; don'tclaimsufficientPyQCUsteadydistribution.
Ouralreadyqueued4callsretained, no discard.

Nativeprimarymetric: originalsolveABIwall (MPImax), shared2RHSstatscountONCE
bybatch_size (don'tsum12duplicatedtimers). Ourresultfieldnative_api_seconds.
Narrowerinternal_seconds onlyaux; Pythonapi_secondsalsoaux. PyQCUsamples
native_seconds sums12ABIcalls+samecolumnnecessaryresidualcorrections. External
NumPychecksoutsideclock. Noone-timesetup/smear/IOincluded.

Usefulread:
ssh ls 'PY R/status.py' (expand). Printsqueue+completedsamples,compactbut~2k.
R/summarize.py deployed: reads6fullresults, computesmedian, validatesall12,
writesR/summary.jsononlywhenall6done (exclusivepath;don'trerunaftercomplete).
R/crosscheck.py deployed: requiresresultclosed, savesnewcomparisonfileexclusive.
Don'trerunsupervisorcrosscheckunderthesameID.
R/export.py deployed: requiresbothsequencecompletion+alltaskspassed/cleanup,
archivesSMALLmetadata/controllers/logs/results (noarrays/libs) toR/export/
evidence.tar.gz andmanifest.jsonwithSHA. Don'trununtilbothfinished.
HostmetadatahelperR/host_metadata.pydeployed, login-host.jsoncreated;compute
hostmetadataNOTyetmade (startupcpuset592exists). Canqueueafterallnumerics.

Needcontinuewaitingandcommunicateconcise<60s, don'tfinalearly. PyQCUnative
128fullestimated~1000s/roundcompute,~1900s/roundlogin;2rounds~35/65min.
Computewhole-nodeexpectedfasterbutDO NOTEXTRAPOLATEactualfinalnumbers.
Finalreport6rowslogin128/compute128/wholecomputefor2solvers,tol1e-8samepoststout,
nativeAPIprimary/setupoutside, firstandallsteady, iteration/residual stats.
CollectarchiveviaWindowsSSHbinarysafe: WSLPython subprocess '/mnt/c/Windows/
System32/OpenSSH/ssh.exe' '-T','-o','ClearAllForwardings=yes','ls','base64 -w0 ...';
base64decodefilteredlines/verifySHA. PowerShell >binary corruptsbytes; avoid.
LocalbasePythonavailableWSLpython3. LocalbackupoldGitbundlevalid,notneededredo.

Needexportrawrecordsafterdone,writeChinesecomparisonreportandJSON,commitnew
branchandpushGitHubifappropriate(originaluserauthorizedupload). Setorigin
https://github.com/WanbaoLi/multigrid.cpp.git sincecurrentrepoonlyhaslocalfetch.
No needmerge. Onlylinkactualfiles. Endwithhonestfull12numbersandprecision,
notearlier4.3unmatchedorours13historicalundernewresourcerows.

BeforefinishSTOPbothworkersaftertasksclosed; Donauresourcesreleaseautomatic.
Originalfrozenkunpengreference skillreadonly; relevantreadpreviouslyapplied.
No newreferenceedits,no numericalsourcechanges. LocalREADMEupdatedprecision
andtworoundPyQCU butfullours16bestmemorydifferencealreadydescribed.
