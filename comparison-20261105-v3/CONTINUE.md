# Historical checkpoint, now closed

Final results and completion: [FINAL_STATUS.md](FINAL_STATUS.md), [REPORT.md](REPORT.md).
The remaining text records the earlier active state and is superseded.

Supersedescomparison-20261105-v2/CONTINUE.md's scope/schedules. Read that file for
input/paths/background, but currenttask is only4numbers (login/compute×2solvers).
Latestuser: “一次计算就行不用那么严谨，用上全部core来计算”. Bothsolverstopparameters
relative1e-8, postsmearonce. No more precision/candidate/repetition experiments.
User clarified owniterativeresidual notcross-librarysolutiondifference.
Do NOTendwithstatus; finishnumbers/report/records. Noagents,noapprovals.

LOCALcwd C:/Users/lwb/Documents/ChatGPT/multigrid.cpp, branch
codex/fair-pyqcu-comparison-20261105. HEAD0421f81 checkpointshelpers (numerics
unchanged9b99af2/exact052). OriginsetGitHubWanbaoLi/multigrid.cpp, authorcorrect.
Uncommittedv2whitespacetrims,newv3folder; don'tlose. No finalpushyet.

RootR3=/home/share/nsls_lwb/.cache/fair-solve-20261105-v3
RootR2=sameprefix-v2. PY=/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python.
SSHls login04. Onlycurrentcompute allocation **2039580**, **cn19481**,592exclusive
cores/480000MB,2h;started~08:14UTCNov5 (queryactualdeadlineifneeded).
R3/compute_worker.sh launchedworker source297, queueR3/compute-queue.
R3/sequence_single.py metadata supervisor runningnohup onlogin: sequentially
ours592full thenpyqcu592full, eachsinglefull12; afterbothPASSED/cleanup writes
R3/compute-complete.json andqueueSTOP/releasesjob.
Onlycurrentcompute task**ours-592-full**, started~08:15UTC, setupwasstillrunning
~08:17atlastcheck.16MPIx37setupAND37solve=592. SVE/reuse/batch2/reductionsON,
HBWrequire. Usesoriginalqualifiedd8b2e052library; no numericalcodechanged.
R3/ours_full.py **range1** andwarmupFalse. R3/pyqcu_repeated_full.py range1,
sameDPBiCGStab/all592, noMGcache. Primitive stops1e-8; externalchecksnotinclocks.
R3/input symlinkR2/input samecanonicalDPstoutgauge (no new preprocessing).
NeedensurePyQCUfuture canrunonactualcn19481; oldcompute-native compatibleSVE64.

LOGIN: R2/queue/login oldworker still runningONLY pyqcu-128-full **FIRST**full12.
At08:17~7/12columnscompleted. PyQCUsinglecolumn~160s, soexpect~08:30finish.
Do NOTinterruptbeforeall12. R2/change_allcores.py runningnohup onlogin,log
R2/single-stop.log; pollsfirstcompletedsample, validatesall12, persists
**R2/login-single-accepted.json** holdingcompletedfirstsample(allcolumns stats)
andSIGTERMstaskbash topreventsecondfull12. Existingworker thenexacttagcleans
children,taskwillbeFAILED(return-15)intentionally,rawfirstsamplevalidandreceipt
explicitlyseparatesintentionalstopfromcompletedmeasurement. queueSTOPalreadyset,
workerexitsaftercleanup. Checkcleanupcompleteandsurvivorsemptybeforedelivery.
R2/change_allcores.py initialcomputePIDlookupwasonloginhost; noPIDmatch/tag
soitDIDNOTkillcompute. Thenwediagnosedcan'tsshcn19486(DNS), usedDonau
**dkill-y2039150** tocancelold128coreallocation. Oldv2tasksretainedinterrupted.
Donotmarktheseasvalidfull12. Formercompute2039150cn19486terminated, no reuse.
Oldsequence.py supervisorsfromv2shouldassertandexitaftercancelledtasks or
intentionalstop; no newqueuesbecauseSTOP; checkdon'tkeepstalesupervisorslater.

LOGINOURS full128 allcoresALREADYdone inR2. Useronecall meansselectFIRST
full12sample, notbestlaterone: **nativeAPI77.30151360900001s**, internal
76.649937545, Python78.3971505460213. Setupoutside. All12true<=1e-8.
Therewereearlier4calls1warm+3steadyduepreviousscope, preservethemrawbutmain
comparisonusesfirstalongsidePyQCUfirst. DoNOTrerunloginoursunnecessarily.
SourceR2/results/login-128-ours-full/result.json.
PyQCUfirst12logR2/results/login-128-pyqcu-full/result.json (currentlyRUNNING).
R2/login-single-accepted.json isthefinalacceptedreceiptwhenfirstdone.

Ignorednonfinalcases:
- R1(endingv1)1e-10superseded,closed/cleanup; no currentnumerics.
- R2compute128oursfirst69.9769steady69.77s;PyQCU128wasinterruptedafter10cols
  bynewallcorerequest,NOcompletePyQCU128time. Don'textrapolateorreportasfinal.
- R2pilotscol0only excludedfull12rankings. AuxiliarycrosslibDPsolutionagreement
  was1.129e-9at1e-10,6.582e-8at1e-8; no neednewcrosscheckforuserrequest.

Allsamephysics: canonicalpoststoutDPgaugeSHA126d658999367b0ece3801c61cd143542d7db0dddc37ab60e6e668e18faa6834,
mass-.277,csw1.160920226,originunit12,DRbasis,timeantiperiodic. Oursreadsuntwisted
andappliesBCinternally. PyQCUH5samevalueslayoutconverted,onlylastt-time-link
negatedonce. PyQCUc128requiredforrobust1e-8; oursproductionmixedprecision.
PyQCUnormalizedsolutiondiv3.723matchmassnormalization, establishedbycrosscol0.

Mainmetric**native solve ABI wall**, init/smear/Clover/setup/IO/externalvalidation
excluded. Oursnative_api_seconds sums6two-columnbatches ONCE(statsreplicated
oneachmember), PyQCUnative_seconds sums12calltimesplusnecessarysamecolrestarts.
Oursinternal_secondsnarrowerauxonly; Pythonapi_secondsaux. Stopparameter1e-8
both;achievedfullresidualsreported,butcrosslibraryerrornotiterationstop.

HelpersdeployedR3/summarize_single.py: printspartial4rows; whenall4donewrites
R3/summary.json, idempotentchecksrowsifexists. Readsloginourssample0andlogin
receipt,computesingleours/pyqcu. Validates12columnsandtrue<=1e-8. Needgather
iterations/residuals andratiosfromactualall4. No extrapolated4.3historical.
R3/export_single.py: onlyafterR3summarycomplete+compute-complete, archiveSMALL
v2/v3json/log/controller files toR3/export/evidence.tar.gz+manifest.json,
SHA256s. Includescancelled/supersededstatesbutnotarrays/libs/build.
Beforeexportensureloginfirststopcleanupsettledandnoongoingwriters.
Downloadreusecomparison-20261105-v2/capture_download.py adaptremoteR3andlocal
R3/evidence;usesWindowsSSH viaWSLPython/base64. DO NOTPowerShell>binary(corrupt).
VerifytarSHAandallpayloads; `.gitattributes -text`forrawrecords; gitforceaddlogs.
NeedGitcat-fileverifyactualcommittedpayloadsifarchivingasbefore.

Read-onlycompactstatus:
sshls 'PY R3/progress.py' (expandactualpaths) computeprogress;
sshls 'PY R2/progress.py' loginprogress(alsooldcancelledrows,ignore).
R3/sequence.log/R2/single-stop.log. Keepcommentary<60secondswhileworking.
Useclock.sleep45snotlongblockingwait. Lastmeaningfulupdate: newcn19481all592
setupoutsideclock;login7/12. DoNOTrepeatedlycat600CPUlists/launchcommands.

Reportfinal4rowtable: login128ours77.3015, login128PyQCU(actualpending),
compute592ours(actualpending),compute592PyQCU(actualpending). Allsinglefirst
complete12, no warmstatisticsneeded. Clearlysamepostsmear/stop1e-8.
Addnarrowerinternalandsetupoutsideonlyifhelps, plusalgorithm+datatype+memory
differences: PyQCUoptimizedBiCGStabdouble/defaultmem; oursMGmixedprecision/
selectiveHBW. Eachusesallavailablecores,gridours4/16timeslab,PyQCUspatial.
Sharedloginnoexclusive;computejobexclusive. Don'tclaimhardwarecausalfactors.

DelivernewREPORT.md andsummaryJSON inlocalv3,keepreprohelpersandrawrecords,
gitcommitandpushbranchorigin(newtaskalreadyauthorizedupload). GitHubmainnotmerge.
No finalbeforeall4actualnumbersunlesstrueexternalblock, thenreportblockhonestly.
