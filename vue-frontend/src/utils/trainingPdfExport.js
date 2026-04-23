/**
 * Сохраняет DOM-фрагмент как многостраничный PDF (html2canvas + jsPDF).
 * Подходит для кириллицы: рендер из уже отрисованной страницы.
 */
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';

export default async function exportElementToPdf(element, fileName) {
  if (!element) {
    return { ok: false, error: 'no_element' };
  }
  const name = (fileName || 'growboard-training-result').replace(/[^\w\u0400-\u04FF-]/g, '_');
  const canvas = await html2canvas(element, {
    scale: 2,
    useCORS: true,
    logging: false,
    backgroundColor: '#ffffff',
    scrollX: 0,
    scrollY: -window.scrollY,
  });
  const imgData = canvas.toDataURL('image/jpeg', 0.92);
  const pdf = new jsPDF('p', 'mm', 'a4');
  const w = pdf.internal.pageSize.getWidth();
  const h = pdf.internal.pageSize.getHeight();
  const imgW = w;
  const imgH = (canvas.height * w) / canvas.width;
  let yOff = 0;
  while (yOff < imgH) {
    if (yOff > 0) pdf.addPage();
    pdf.addImage(imgData, 'JPEG', 0, -yOff, imgW, imgH);
    yOff += h;
  }
  pdf.save(`${name}.pdf`);
  return { ok: true };
}
