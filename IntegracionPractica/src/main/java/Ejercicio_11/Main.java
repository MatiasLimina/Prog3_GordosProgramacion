package Ejercicio_11;

import java.util.Arrays;
import java.util.Date;

public class Main {
    public static void main(String[] args) {
        System.out.println("=== DEMO EJERCICIO 11: COSMÉTICA NATURAL ==-\n");

        // 1. Fechas de referencia
        Date fechaUltimaReunion = new Date(System.currentTimeMillis() - 30L * 24 * 60 * 60 * 1000); // Hace 30 días
        Date fechaProximaReunion = new Date(System.currentTimeMillis() + 30L * 24 * 60 * 60 * 1000); // En 30 días
        Date hoy = new Date();

        // 2. Crear Productos
        Producto cremaFacial = new Producto("Crema Hidratante Facial", 4500.0);
        Producto serum = new Producto("Sérum Vitamina C", 7200.0);
        Producto protectorSolar = new Producto("Protector Solar FPS 50", 6000.0);

        // 3. Crear Equipo y Líder
        Equipo equipoNorte = new Equipo("Equipo Norte Estrellas");
        Lider lider = new Lider(
                "Carla Pérez",
                "Av. Libertador 1234",
                "+54 9 11 5555-1234",
                new Date(75, 5, 12),
                "27-25432109-4",
                new Date(120, 0, 15), // 2020
                0.15, // 15% comisión
                new Date(122, 5, 10), // 2022
                equipoNorte
        );

        // 4. Crear Vendedores del Equipo
        Vendedor vendedor1 = new Vendedor(
                "Juan Gómez",
                "Calle Falsa 456",
                "+54 9 11 4444-5678",
                new Date(88, 2, 20),
                "20-31234567-9",
                new Date(123, 2, 1),
                0.10 // 10% comisión
        );

        Vendedor vendedor2 = new Vendedor(
                "Ana Torres",
                "San Martín 789",
                "+54 9 11 3333-9876",
                new Date(92, 8, 5),
                "27-34567890-1",
                new Date(123, 5, 10),
                0.10 // 10% comisión
        );

        equipoNorte.agregarVendedor(vendedor1);
        equipoNorte.agregarVendedor(vendedor2);

        // 5. Crear Clientes y agregarlos a carteras
        Cliente cliente1 = new Cliente("Sofía Benítez", "Belgrano 100", "+54 9 11 2222-1111", new Date(95, 1, 1), new Date());
        Cliente cliente2 = new Cliente("Diego Rivas", "Mitre 200", "+54 9 11 1111-2222", new Date(90, 4, 15), new Date());

        vendedor1.agregarCliente(cliente1);
        lider.agregarCliente(cliente2);

        // 6. Emitir Tickets de Venta
        // Vendedor 1 vende 2 cremas y 1 sérum
        TicketVenta t1 = new TicketVenta(hoy, cremaFacial.getPrecioVenta(), cremaFacial, vendedor1);
        t1.setCliente(cliente1);

        TicketVenta t2 = new TicketVenta(hoy, serum.getPrecioVenta(), serum, vendedor1);
        t2.setCliente(cliente1);

        // Vendedor 2 vende 1 protector solar
        TicketVenta t3 = new TicketVenta(hoy, protectorSolar.getPrecioVenta(), protectorSolar, vendedor2);

        // Líder realiza venta directa (1 sérum)
        TicketVenta t4 = new TicketVenta(hoy, serum.getPrecioVenta(), serum, lider);
        t4.setCliente(cliente2);

        // 7. Reunión General Mensual
        ReunionGeneral reunion = new ReunionGeneral(fechaUltimaReunion, fechaProximaReunion);
        reunion.registrarAsistente(lider);
        reunion.registrarAsistente(vendedor1);
        reunion.registrarAsistente(vendedor2);

        // 8. Cálculo de Comisiones (Rendición en reunión)
        System.out.println("--- RENDICIÓN DE COMISIONES (Desde última reunión) ---");
        
        double comV1 = vendedor1.calcularComision(fechaUltimaReunion);
        System.out.println("Comisión Vendedor 1 (" + vendedor1.getNombre() + "): $" + comV1);

        double comV2 = vendedor2.calcularComision(fechaUltimaReunion);
        System.out.println("Comisión Vendedor 2 (" + vendedor2.getNombre() + "): $" + comV2);

        double comLider = lider.calcularComision(fechaUltimaReunion);
        System.out.println("Comisión Líder (" + lider.getNombre() + ") [Incluye ventas propias + % de equipo]: $" + comLider);

        System.out.println("\n--- DETALLES DE LA REUNIÓN GENERAL ---");
        System.out.println("Fecha Última Reunión: " + reunion.getFechaUltimaReunion());
        System.out.println("Fecha Próxima Reunión: " + reunion.getFechaProximaReunion());
        System.out.println("Total Asistentes: " + reunion.getAsistentes().size());

        System.out.println("\n--- DEMO EJERCICIO 11 COMPLETADA EXITOSAMENTE ---");
    }
}
