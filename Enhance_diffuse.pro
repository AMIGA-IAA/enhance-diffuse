pro Enhance_diffuse


;Reading the conf page
READCOL,'Conf_page.dat',conf_page,/SILENT


noise_tilesize=STRCOMPRESS(conf_page[0], /REMOVE_ALL)
noise_qthresh=STRCOMPRESS(conf_page[1], /REMOVE_ALL)
noise_interpnumngb=STRCOMPRESS(FIX(conf_page[2]), /REMOVE_ALL)
noise_detgrowquant=STRCOMPRESS(conf_page[3], /REMOVE_ALL)

smo=STRCOMPRESS(conf_page[4], /REMOVE_ALL)

; I obtain a list of the input images
spawn,'ls Inputs/ > list_imas.txt'

; list_imas is the list of the name of the images, while N_imas is an integer with the number of images
READCOL,'list_imas.txt',list_imas,F='A',/SILENT
N_imas=SIZE(list_imas)
N_imas=FIX(N_imas[1])

;Getting the size of the input images
name=STRCOMPRESS(list_imas[0], /REMOVE_ALL)
name='Inputs/'+name
print,name
ima_0 = READFITS(name,h_ima)
tama=SIZE(ima_0)

;Creating the masks and total image
mask_total=fltarr(tama[1],tama[2])
Ima_total=fltarr(tama[1],tama[2])


;I create a loop for the masking of each input image

for nn=0, N_imas-1 do begin

  name=STRCOMPRESS(list_imas[nn], /REMOVE_ALL)
  name='Inputs/'+name
  print,name
  spawn,'cp '+name+' ima_temp.fits'
  ima=readfits('ima_temp.fits',h_ima)
  Ima_total=Ima_total+ima

  ;Run noisechisel
  run='astnoisechisel ima_temp.fits -h0 --tilesize='+noise_tilesize+','+noise_tilesize+' --qthresh='+noise_qthresh+' --interpnumngb='+noise_interpnumngb+' --detgrowquant='+noise_detgrowquant
  spawn,run
  noise_ima=readfits('ima_temp_detected.fits', h_mask,ext=2)
  mask_total=mask_total+noise_ima
  
  ;Run sextractor
  spawn,'sextractor ima_temp.fits -c Params/sex_point.conf'
  noise_ima_sex=readfits('check.fits')
  mask_total=mask_total+noise_ima_sex

endfor

;I mask the total image
for ii=0,tama[1]-1 do begin
  for jj=0,tama[2]-1 do begin
    if (mask_total[ii,jj] NE 0) then Ima_total[ii,jj]=!Values.F_NaN
  endfor
endfor

writefits,'Ima_total.fits',Ima_total,h_ima
writefits,'Mask.fits',mask_total,h_mask

spawn,'swarp Ima_total.fits -c Params/swarp.conf'
Ima_rebin=readfits('coadd.fits',h_rebin)
tama_rebin=SIZE(Ima_rebin)

;I mask the rebin image
for ii=0,tama_rebin[1]-1 do begin
  for jj=0,tama_rebin[2]-1 do begin
    if (Ima_rebin[ii,jj] EQ 0) then Ima_rebin[ii,jj]=!Values.F_NaN
  endfor
endfor

;Gauss smoothing
Ima_enhanced=GAUSS_SMOOTH(Ima_rebin,FIX(smo),/EDGE_TRUNCATE,/NAN)

writefits,'Enhanced.fits',Ima_enhanced,h_rebin

spawn,'rm list_imas.txt'
spawn,'rm ima_temp.fits'
spawn,'rm test.cat'
spawn,'rm check.fits'
spawn,'rm ima_temp_detected.fits'
spawn,'rm coadd.fits'
spawn,'rm coadd.weight.fits'
spawn,'rm swarp.xml'





end
