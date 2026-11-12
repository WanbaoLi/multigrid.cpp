# Active single-source tuning; must continue actual experiments

Latest human: onlysingle source/single configuration full12. DO NOT sourcegroup
parallelism or multiconfiguration. Relative stopping1e-8, samepoststoutgauge,
pure solve primary, setupIOexcluded. User wants continuedoptimization plus
answerwhetherFP64. Alreadyansweredcommentary: mixed,hotprecondFP32,reliable
residualFP64; userbeliefhighFP64is hypothesis,notmeasuredperformancepromise.
No agents. No approval. Keepupdates<60s, don'tfinalwhiletasksactive.

cwd C:/Users/lwb/Documents/ChatGPT/multigrid.cpp, branch
codex/lingsheng-single-source-20261105 frome56704c(previousfaircomparisoncomplete).
CurrentcommittedHEAD96be7184ea565d084d8b38b9afc65257172b3293.
Sourcechangessofarintroduce**LQCD_OUTER_FLOAT** productionvalidatedoption:
- Impl::outer_float bool(defaulttrue) inhiearchy.hpp.
- configure_solve() appendname/value/range0/1 toexistingcollectivevalidation;
  fallbackNATIVE_OUTER_FLOATdefaultretainedforbench_nativelegacyonly.
- solver.cpp andbatched_solver.cpp branchonvalidatedimplflag.
- PythonSOLVE_TUNING_KEYSaddsnewflag.
- tests/runtime/test_mg_tuning.py extendedone-hierarchyouter0/1,scalar+batch
  independentplane-waveexactsolutions,invalid/rankmismatch+recovery.
ProductionNATIVE_*rejectionSTILLUNCHANGED. FullFP64preconditionerNOTimplemented.
LQCD_OUTER_FLOAT=0 isFP64outerGCR,stillFP32preconditioning andbatchentryfalls
backtosequentialRHS. Needmixed-singletoisolatebatchcostfromprecision.
Default1numericpathunchanged.

ONLYcurrentcompute**job2040242**, exclusive592cores/480000MB,4h. Actualhost
**cn19486**. Started~09:21UTCNov5;queryexactdeadlineifneeded(djob-J-lID).
RootR=/home/share/nsls_lwb/.cache/fair-solve-20261105-v4
PY=/home/share/nsls_lwb/.cache/multigrid-arm-20261025-env/bin/python
OriginalROOT=/home/share/nsls_lwb/.cache/mg-opt-20261103.
R/input symlinksamecanonicalDPpoststoutR3/input, unchanged.
CanonicalSHA126d658999367b0ece3801c61cd143542d7db0dddc37ab60e6e668e18faa6834,
mass-.277/csw1.160920226/originunit/timeantiperiodic/DR/massnormalization.
All59216MPI×37, no other numericalrunsonthisnodefromthischat.
QueueR/compute-queue, originalsource297 existingworker.py, taggedcleanup.
Workerhas~14000slifetime/idle1800. NO STOPyet, leaveavailableforfollowups.

Initialtrial**baseline-full12FAILED17sBEFOREnumerics**, becauseIset
NATIVE_OUTER_FLOAT=1whichproductionAPIrejects. Preservedoriginaldriver/source/
task/log. Don'trelabelpass. Explainederror. NewLQCD_OUTER_FLOATformaloptionabove
iscorrectimplementation, notguardbypass. No NATIVEoverrideinnewvalidatedruns.

ACTUALnewsourceR/source-outer cleanHEAD96be7184… fetchedlocalGitbundlebased297.
BuildR/build-outer/liblqcd_cpu.so (SHAneededwhenresultsarrive).
BuildscriptR/build_outer.sh pinsHEAD96be7184, GCC10sysroot+SDK12runtime,
KUPLON,HMPI25.1,ReleaseO3native, pin_build16parallel. Existingtestedtoolchain.
Task**010-build-outer-option PASSED**485s, cleanupempty; actual23selectedCTest
ALLPASSED419.03s, inclMPI2, batch12MPI2, coarsebatchserial/MPI2, runtime_batch,
andnewMGtuningtest29.76s. It finished~09:37UTC. No needrerunwithoutnewchanges.
R/outer-build-passed exists. Sourcebuildnewactualtestslegitimate.

NewR/sequence_validated.py supervisor(nohup onlogin, logR/validated-sequence.log)
waitsclosedbuildandthenqueues3FRESHprocesses sequentially:
1 baseline-v2: LQCD_OUTER_FLOAT1,batch2
2 double-outer-v2: LQCD_OUTER_FLOAT0,batch2APIsequentialnativefallback
3 mixed-single-v2: LQCD_OUTER_FLOAT1,batch1
R/run_outer_validated.sh usesnewbuild+newsource,setsLQCD_HBW_ALLOC=require,
verbose0,37setup+37solve,oldretainSVE/reuse/coarsereduce/spatialoverlapflags.
Eachprocessownsetup+onefull12zero-startcall. No repeatsperlatestuserpreference.
Timeout1800each. Afterall3writesR/validated-complete.json, DOESNOTSTOPworker.
**Lastcheck~09:37UTC**buildclosed, baseline-v2shouldjuststart; latesttoolcall
outputnotyetrecordedhere (readprogress). Noactualprecisionfull12numbersyet.

R/ours_mode.py drivernewsourcepythonpackage, sameorigin12fullsolve tol1e-8.
Capturesinternal_seconds,native_api_seconds(sharedbatchtimeronlyONCE),
api_seconds Pythonfullcall,stats12/iteration/residual;recordouter_float/rhsbatch.
EachresultR/results/{mode}/result.json. Fullranklocalpropagator savedas
propagator-rank00000..15.npy OUTSIDEclock, forfull12solutionalignment.
All12true residualassert<=1e-8. NeedcompareALL12relativeoutputerror<=1e-6 vs
same-nodebaseline usingrankarrays; donothasharraysconcurrentlywithordinaryruns.
Currentprofilebasis:155oldsampleGOMP~40%usercycles(notwall),fine/localhotspots,
only32SAPcolorblocktasksperrankvs37threads. Historicaldefault32solvebest
~13.33s/37allcore14.39s. Userprefallcoresfromcomparison;currentprecision
comparisonuses37consistently. DoNOTclaimtheoryFP64peakimpliesfasteralgorithm.

Mainphysicsoptimizationnotyetachieved/newbestnotadopted. Old052libd8b2e052
andoriginalsource5fe1b5f/defaultmixsafe. Needcontinuetoactual3precisionresults.
IfFP64outerloses, don'tabandononlyonce: separatebatchlosscostvsmixed-single,
readstageprofileorcodegen, thenjustifiedcandidate (e.g.batchedFP64outersharing
existingapply_vcycle_batch) ratherthanswitchallfloatstodoubleblindly.
Onepossiblenextcandidate: existingFP64outerGCRsingleiterationprecondition
encodeFP32/Vcycle/decode, thenDPapply/dot/update; currentbatchfallbackloses
reuse. ImplementindependentDPKrylovhistoriesbutbatchthefloatVcycleforsame12
RHS, retaindoublefulloperator/stop, predicateactivecolumns/zero/restart; needs
actualprofile/supportbeforeimplementation. Notyetwritten. Anothercandidate
useDPvectorfusedreductionsbutneedsactualbottleneck. Focusendtoend12pureAPI.

Localnewuntrackedbenchmarks/hardware/ andoutputs/ appearedfromOTHERchat/shared
workspace. DON'Tadd/remove/alterthem orassumethisagentcreatedthem. Onlystage
ownv4+explicitnumericalfiles. Somev4helpersuntracked(build_outer,ours_mode,
run_outer_validated,sequence_validated,publish_build); preserve.
outer-source.bundlelocalbinary5MB+untracked NOTrequiredcommittoGit.
Readreference frozenkunpengskill alreadyappliedthisconversation;keepreadonly.

HelperR/progress.py printsclosed/runningstatus+samples. Use
sshls 'PY R/progress.py' expanded. AvoidbigCPUlistorfullLQCDstdoutlaunchline.
TasklogR/compute-queue/{id}.log, sequence log. Existingworkercleanupdetects
taggeddescendants. Failedinitialoldsequence.py stoppedwithassert; doNOTrestart.

Needfinaldeliveryafterboundedactualoptimization: bestcorrectsingle-sourcecode,
results+precisions+allfailedrounds, no unmeasuredclaims. Commit/pushnewbranch
whenconcrete, no PRmerge. Useruploadpriorauthorized. LinkChineseclearreport,
explainFP32/64andwhydecidedfromactualwhole12time. No formulaunexplainedletters.
Stopworker/releaseallocationonlywhenallnecessaryrunscompleted; blockedresources
reporthonestly. Currentallocationavailable,continueautonomously.
